import logging
import os
import sys
from arx.parser import PrototypeAST, TreeAST
from typing import List, Any

from llvmlite import binding as llvm

from arx.ast import (
    BinaryExprAST,
    CallExprAST,
    ExprAST,
    FloatExprAST,
    ForExprAST,
    FunctionAST,
    IfExprAST,
    PrototypeAST,
    ReturnExprAST,
    TreeAST,
    UnaryExprAST,
    VarExprAST,
    VariableExprAST,
    Visitor,
)

from arx.codegen.base import CodeGenBase
from arx.codegen.arx_llvm import ArxLLVM
from arx.logs import LogErrorV
from arx.io import ArxFile
from arx.lexer import Lexer

logging.basicConfig(level=logging.INFO)
LOG = logging.getLogger(__name__)


def string_join(elements: List[str], delimiter: str) -> str:
    """
    Join the elements in the list with the given delimiter.

    Args:
        elements: The list of elements to join.
        delimiter: The delimiter to use for joining.

    Returns:
        The joined string.
    """
    if not elements:
        return ""

    return delimiter.join(elements)


INPUT_FILE: str = ""
OUTPUT_FILE: str = ""
ARX_VERSION: str = ""
IS_BUILD_LIB: bool = True


class ObjectGeneratorVisitor(Visitor):
    def __init__(self):
        self.result_val: Value = None
        self.result_func: Function = None

    def visit_float_expr(self, expr: FloatExprAST):
        """
        Code generation for FloatExprAST.

        Args:
            expr: The FloatExprAST instance
        """
        self.result_val = llvm.ir.Constant(ArxLLVM.FLOAT_TYPE, expr.val)

    def visit_variable_expr(self, expr: VariableExprAST):
        """
        Code generation for VariableExprAST.

        Args:
            expr: The VariableExprAST instance
        """
        expr_var = ArxLLVM.named_values.get(expr.name)

        if not expr_var:
            msg = f"Unknown variable name: {expr.name}"
            self.result_val = LogErrorV(msg)
            return

        self.result_val = ArxLLVM.ir_builder.load(expr_var, expr.name)

    def visit_unary_expr(self, expr: UnaryExprAST):
        """
        Code generation for UnaryExprAST.

        Args:
            expr: The UnaryExprAST instance
        """
        expr.operand.accept(self)
        operand_value = self.result_val

        if not operand_value:
            self.result_val = None
            return

        self.get_function("unary" + expr.op_code)
        fn = self.result_func
        if not fn:
            self.result_val = LogErrorV("Unknown unary operator")
            return

        self.result_val = ArxLLVM.ir_builder.CreateCall(
            fn, operand_value, "unop"
        )

    def visit_binary_expr(self, expr: BinaryExprAST):
        """
        Code generation for BinaryExprAST.

        Args:
            expr: The BinaryExprAST instance
        """
        if expr.op == "=":
            # Special case '=' because we don't want to emit the lhs as an expression.
            # Assignment requires the lhs to be an identifier.
            # This assumes we're building without RTTI because LLVM builds that way by default.
            # If you build LLVM with RTTI, this can be changed to a dynamic_cast for automatic error checking.
            var_lhs = cast(VariableExprAST, expr.lhs)

            if not var_lhs:
                self.result_val = LogErrorV(
                    "destination of '=' must be a variable"
                )
                return

            # Codegen the rhs.
            expr.rhs.accept(self)
            val = self.result_val

            if not val:
                self.result_val = None
                return

            # Look up the name.
            variable = ArxLLVM.named_values[var_lhs.get_name()]

            if not variable:
                self.result_val = LogErrorV("Unknown variable name")
                return

            ArxLLVM.ir_builder.CreateStore(val, variable)
            self.result_val = val

        expr.lhs.accept(self)
        llvm_val_lhs = self.result_val
        expr.rhs.accept(self)
        llvm_val_rhs = self.result_val

        if not llvm_val_lhs or not llvm_val_rhs:
            self.result_val = None
            return

        if expr.op == "+":
            self.result_val = ArxLLVM.ir_builder.CreateFAdd(
                llvm_val_lhs, llvm_val_rhs, "addtmp"
            )
        elif expr.op == "-":
            self.result_val = ArxLLVM.ir_builder.CreateFSub(
                llvm_val_lhs, llvm_val_rhs, "subtmp"
            )
        elif expr.op == "*":
            self.result_val = ArxLLVM.ir_builder.CreateFMul(
                llvm_val_lhs, llvm_val_rhs, "multmp"
            )
        elif expr.op == "<":
            llvm_val_lhs = ArxLLVM.ir_builder.CreateFCmpULT(
                llvm_val_lhs, llvm_val_rhs, "cmptmp"
            )
            # Convert bool 0/1 to float 0.0 or 1.0
            self.result_val = ArxLLVM.ir_builder.CreateUIToFP(
                llvm_val_lhs, ArxLLVM.FLOAT_TYPE, "booltmp"
            )
        else:
            # If it wasn't a builtin binary operator, it must be a user defined one. Emit a call to it.
            self.get_function("binary" + expr.op)
            fn = self.result_func
            assert fn, "binary operator not found!"

            Ops = [llvm_val_lhs, llvm_val_rhs]
            self.result_val = ArxLLVM.ir_builder.CreateCall(fn, Ops, "binop")

    def visit_call_expr(self, expr: CallExprAST):
        """
        Code generation for CallExprAST.

        Args:
            expr: The CallExprAST instance
        """
        self.get_function(expr.callee)
        callee_f = self.result_func

        if not callee_f:
            self.result_val = LogErrorV("Unknown function referenced")
            return

        if callee_f.arg_size() != len(expr.args):
            self.result_val = LogErrorV("Incorrect # arguments passed")
            return

        args_v = []
        for arg in expr.args:
            arg.accept(self)
            args_v_item = self.result_val
            args_v.append(args_v_item)
            if not args_v_item:
                self.result_val = None
                return

        self.result_val = ArxLLVM.ir_builder.CreateCall(
            callee_f, args_v, "calltmp"
        )

    def visit_ir_expr(self, expr: IfExprAST):
        """
        Code generation for IfExprAST.

        Args:
            expr: The IfExprAST instance
        """
        expr.cond.accept(self)
        cond_v = self.result_val

        if not cond_v:
            self.result_val = None
            return

        # Convert condition to a bool by comparing non-equal to 0.0.
        cond_v = ArxLLVM.ir_builder.CreateFCmpONE(
            cond_v,
            llvm.ir.Constant(ArxLLVM.FLOAT_TYPE, 0.0),
            "ifcond",
        )

        fn = ArxLLVM.ir_builder.GetInsertBlock().getParent()

        # Create blocks for the then and else cases. Insert the 'then' block
        # at the end of the function.
        then_bb = llvm.BasicBlock.Create(ArxLLVM.context, "then", fn)
        else_bb = llvm.BasicBlock.Create(ArxLLVM.context, "else")
        merge_bb = llvm.BasicBlock.Create(ArxLLVM.context, "ifcont")

        ArxLLVM.ir_builder.CreateCondBr(cond_v, then_bb, else_bb)

        # Emit then value.
        ArxLLVM.ir_builder.SetInsertPoint(then_bb)

        expr.then.accept(self)
        then_v = self.result_val
        if not then_v:
            self.result_val = None
            return

        ArxLLVM.ir_builder.CreateBr(merge_bb)
        # Codegen of 'then' can change the current block, update then_bb for the PHI.
        then_bb = ArxLLVM.ir_builder.GetInsertBlock()

        # Emit else block.
        fn.getBasicBlockList().push_back(else_bb)
        ArxLLVM.ir_builder.SetInsertPoint(else_bb)

        expr.else_.accept(self)
        else_v = self.result_val
        if not else_v:
            self.result_val = None
            return

        ArxLLVM.ir_builder.CreateBr(merge_bb)
        # Codegen of 'else_' can change the current block, update else_bb for the PHI.
        else_bb = ArxLLVM.ir_builder.GetInsertBlock()

        # Emit merge block.
        fn.getBasicBlockList().push_back(merge_bb)
        ArxLLVM.ir_builder.SetInsertPoint(merge_bb)
        pn = ArxLLVM.ir_builder.CreatePHI(ArxLLVM.FLOAT_TYPE, 2, "iftmp")

        pn.addIncoming(then_v, then_bb)
        pn.addIncoming(else_v, else_bb)

        self.result_val = pn
        return

    def visit_for_expr(self, expr: ForExprAST):
        """
        Code generation for ForExprAST.

        Args:
            expr: The ForExprAST instance.
        """
        fn = ArxLLVM.ir_builder.GetInsertBlock().getParent()

        # Create an alloca for the variable in the entry block.
        # TODO: maybe it would be safe to change it to void
        alloca = self.create_entry_block_alloca(fn, expr.var_name, "float")

        # Emit the start code first, without 'variable' in scope.
        expr.start.accept(self)
        start_val = self.result_val
        if not start_val:
            self.result_val = None
            return

        # Store the value into the alloca.
        ArxLLVM.ir_builder.CreateStore(start_val, alloca)

        # Make the new basic block for the loop header, inserting after
        # current block.
        loop_bb = llvm.BasicBlock.Create(ArxLLVM.context, "loop", fn)

        # Insert an explicit fall through from the current block to the
        # loop_bb.
        ArxLLVM.ir_builder.CreateBr(loop_bb)

        # Start insertion in loop_bb.
        ArxLLVM.ir_builder.SetInsertPoint(loop_bb)

        # Within the loop, the variable is defined equal to the PHI node.
        # If it shadows an existing variable, we have to restore it, so save it now.
        old_val = ArxLLVM.named_values.get(expr.var_name)
        ArxLLVM.named_values[expr.var_name] = alloca

        # Emit the body of the loop. This, like any other expr, can change
        # the current basic_block. Note that we ignore the value computed by the
        # body, but don't allow an error.
        expr.body.accept(self)
        body_val = self.result_val

        if not body_val:
            self.result_val = None
            return

        # Emit the step value.
        step_val = None
        if expr.step:
            expr.step.accept(self)
            step_val = self.result_val
            if not step_val:
                self.result_val = None
                return
        else:
            # If not specified, use 1.0.
            step_val = llvm.ir.Constant(ArxLLVM.FLOAT_TYPE, 1.0)

        # Compute the end condition.
        expr.end.accept(self)
        end_cond = self.result_val
        if not end_cond:
            self.result_val = None
            return

        # Reload, increment, and restore the alloca. This handles the case
        # where the body of the loop mutates the variable.
        cur_var = ArxLLVM.ir_builder.CreateLoad(
            ArxLLVM.FLOAT_TYPE, alloca, expr.var_name
        )
        next_var = ArxLLVM.ir_builder.CreateFAdd(cur_var, step_val, "nextvar")
        ArxLLVM.ir_builder.CreateStore(next_var, alloca)

        # Convert condition to a bool by comparing non-equal to 0.0.
        end_cond = ArxLLVM.ir_builder.CreateFCmpONE(
            end_cond,
            llvm.ir.Constant(ArxLLVM.FLOAT_TYPE, 0.0),
            "loopcond",
        )

        # Create the "after loop" block and insert it.
        after_bb = llvm.BasicBlock.Create(ArxLLVM.context, "afterloop", fn)

        # Insert the conditional branch into the end of loop_bb.
        ArxLLVM.ir_builder.CreateCondBr(end_cond, loop_bb, after_bb)

        # Any new code will be inserted in after_bb.
        ArxLLVM.ir_builder.SetInsertPoint(after_bb)

        # Restore the unshadowed variable.
        if old_val:
            ArxLLVM.named_values[expr.var_name] = old_val
        else:
            ArxLLVM.named_values.pop(expr.var_name, None)

        # for expr always returns 0.0.
        self.result_val = llvm.ir.Constant.getNullValue(ArxLLVM.FLOAT_TYPE)

    def visit_var_expr(self, expr: VarExprAST):
        """
        Code generation for VarExprAST.

        Args:
            expr: The VarExprAST instance.
        """
        old_bindings: List[llvm.AllocaInst] = []

        fn = ArxLLVM.ir_builder.GetInsertBlock().getParent()

        # Register all variables and emit their initializer.
        for var_name, init in expr.var_names.items():
            # Emit the initializer before adding the variable to scope, this
            # prevents the initializer from referencing the variable itself, and
            # permits stuff like this:
            #  var a = 1 in
            #    var a = a in ...   # refers to outer 'a'.

            init_val: llvm.Value
            if init:
                init.accept(self)
                init_val = self.result_val
                if not init_val:
                    self.result_val = None
                    return
            else:  # If not specified, use 0.0.
                init_val = llvm.ir.Constant(ArxLLVM.FLOAT_TYPE, 0.0)

            # TODO: replace "float" for the actual type_name from the argument
            alloca = create_entry_block_alloca(fn, var_name, "float")
            ArxLLVM.ir_builder.CreateStore(init_val, alloca)

            # Remember the old variable binding so that we can restore the
            # binding when we unrecurse.
            old_bindings.append(ArxLLVM.named_values.get(var_name))

            # Remember this binding.
            ArxLLVM.named_values[var_name] = alloca

        # Codegen the body, now that all vars are in scope.
        expr.body.accept(self)
        body_val = self.result_val
        if not body_val:
            self.result_val = None
            return

        # Pop all our variables from scope.
        for i, (var_name, _) in enumerate(expr.var_names.items()):
            ArxLLVM.named_values[var_name] = old_bindings[i]

        # Return the body computation.
        self.result_val = body_val

    def visit_prototype(self, expr: PrototypeAST):
        """
        Code generation for PrototypeExprAST.

        Args:
            expr: The PrototypeAST instance.
        """
        args_type = [ArxLLVM.FLOAT_TYPE] * len(expr.args)
        return_type = ArxLLVM.get_data_type("float")

        fn_type = llvm.ir.FunctionType(return_type, args_type, False)

        fn = llvm.ir.Function(ArxLLVM.module, fn_type, expr.name)

        # Set names for all arguments.
        idx = 0
        for arg in fn.args:
            arg.name = expr.args[idx].name
            idx += 1

        self.result_func = fn

    def visit_function(self, expr: FunctionAST):
        """
        Code generation for FunctionExprAST.

        Transfer ownership of the prototype to the ArxLLVM::function_protos map,
        but keep a reference to it for use below.

        Args:
            expr: The FunctionAST instance.
        """
        proto = expr.proto
        ArxLLVM.function_protos[expr.proto.get_name()] = expr.proto
        self.get_function(proto.get_name())
        fn = self.result_func

        if not fn:
            self.result_func = None
            return

        # Create a new basic block to start insertion into.
        basic_block = fn.append_basic_block("entry")

        # Record the function arguments in the named_values map.
        ArxLLVM.named_values.clear()

        builder = llvm.ir.IRBuilder(basic_block)

        for llvm_arg in fn.args:
            # Create an alloca for this variable.
            alloca = builder.alloca(ArxLLVM.FLOAT_TYPE, llvm_arg._get_name())

            # Store the initial value into the alloca.
            builder.store(llvm_arg, alloca)

            # Add arguments to variable symbol table.
            ArxLLVM.named_values[str(llvm_arg._get_name())] = alloca

        expr.body.accept(self)

        # Validate the generated code, checking for consistency.
        self.result_func = fn
        if self.result_val:
            builder.ret(self.result_val)
            return
        builder.ret(llvm.ir.Constant(ArxLLVM.FLOAT_TYPE, 0))

    def visit_return_expr(self, expr: ReturnExprAST):
        """
        Code generation for ReturnExprAST.

        Args:
            expr: The ReturnExprAST instance.
        """
        llvm_return_val = self.result_val

        if llvm_return_val:
            ArxLLVM.ir_builder.CreateRet(llvm_return_val)

    def clean(self):
        """
        Set to None result_val and result_func in order to avoid trash.
        """
        self.result_val = None
        self.result_func = None

    def get_function(self, name: str):
        """
        Put the function defined by the given name to result_func.

        Args:
            name: Function name
        """
        if name in ArxLLVM.module.globals:
            fn = ArxLLVM.module.get_global(name)
            self.result_func = fn
            return

        if name in ArxLLVM.function_protos:
            ArxLLVM.function_protos[name].accept(self)

    def create_entry_block_alloca(
        self, fn: llvm.ir.Function, var_name: str, type_name: str
    ) -> Any:  # llvm.AllocaInst
        """
        Create the Entry Block Allocation.

        Args:
            fn: The llvm function
            var_name: The variable name
            type_name: The type name

        Returns:
            An llvm allocation instance.

        create_entry_block_alloca - Create an alloca instruction in the entry
        block of the function. This is used for mutable variables, etc.
        """
        tmp_builder = llvm.ir.IRBuilder()
        tmp_builder.position_at_start(fn.entry_basic_block)
        return tmp_builder.alloca(
            ArxLLVM.get_data_type(type_name), None, var_name
        )

    def visit_tree(self, ast: TreeAST):
        """
        The main loop that walks the AST.
        top ::= definition | external | expression | ';'

        Args:
            ast: The TreeAST instance.
        """
        for node in ast.nodes:
            node.accept(self)


class ObjectGenerator(CodeGenBase):
    output_file: str = ""
    input_file: str = ""

    def __init__(self):
        self.codegen = ObjectGeneratorVisitor()

        self.initialize()

        self._add_builtins(ArxLLVM.module)

    def initialize(self):
        """
        Initialize LLVM Module And PassManager.
        """
        ArxLLVM.initialize()

        logging.info("target_triple")
        self.target = llvm.Target.from_default_triple()
        self.target_machine = self.target.create_target_machine(
            codemodel="small"
        )

        self.output_file = "tmp.o"
        self.input_file = ""

    def _add_builtins(self, module: llvm.ir.module.Module):
        # The C++ tutorial adds putchard() simply by defining it in the host C++
        # code, which is then accessible to the JIT. It doesn't work as simply
        # for us; but luckily it's very easy to define new "C level" functions
        # for our JITed code to use - just emit them as LLVM IR. This is what
        # this method does.

        # Add the declaration of putchar
        putchar_ty = llvm.ir.FunctionType(
            ArxLLVM.INT32_TYPE, [ArxLLVM.INT32_TYPE]
        )
        putchar = llvm.ir.Function(module, putchar_ty, "putchar")

        # Add putchard
        putchard_ty = llvm.ir.FunctionType(
            ArxLLVM.FLOAT_TYPE, [ArxLLVM.FLOAT_TYPE]
        )
        putchard = llvm.ir.Function(module, putchard_ty, "putchard")

        irbuilder = llvm.ir.IRBuilder(putchard.append_basic_block("entry"))

        ival = irbuilder.fptoui(
            putchard.args[0], ArxLLVM.INT32_TYPE, "intcast"
        )

        irbuilder.call(putchar, [ival])
        irbuilder.ret(llvm.ir.Constant(ArxLLVM.FLOAT_TYPE, 0))

    def evaluate(self, tree_ast: TreeAST) -> int:
        """
        Compile an AST to an object file.

        Args:
            tree_ast: The AST tree object.

        Returns:
            int: The compilation result.
        """

        logging.info("Starting main_loop")
        self.codegen.visit_tree(tree_ast)

        # Convert LLVM IR into in-memory representation
        result_mod = llvm.parse_assembly(str(ArxLLVM.module))
        result_object = self.target_machine.emit_object(result_mod)

        if self.output_file == "":
            self.output_file = self.input_file + ".o"

        # Output object code to a file.
        with open(self.output_file, "wb") as obj_file:
            obj_file.write(result_object)
            print("Wrote " + self.output_file)

        if IS_BUILD_LIB:
            return 0

        # generate an executable file

        linker_path = "clang++"
        executable_path = self.input_file + "c"
        # note: it just has a purpose to demonstrate an initial implementation
        #       it will be improved in a follow-up PR
        content = (
            "#include <iostream>\n"
            "int main() {\n"
            '  std::cout << "ARX[WARNING]: '
            'This is an empty executable file" << std::endl;\n'
            "}\n"
        )

        main_cpp_path = ArxFile.create_tmp_file(content)

        if main_cpp_path == "":
            llvm.errs() << "ARX[FAIL]: Executable file was not created."
            return 1

        # Example (running it from a shell prompt):
        # clang++ \
        #   ${CLANG_EXTRAS} \
        #   ${DEBUG_FLAGS} \
        #   -fPIC \
        #   -std=c++20 \
        #   "${TEST_DIR_PATH}/integration/${test_name}.cpp" \
        #   ${OBJECT_FILE} \
        #   -o "${TMP_DIR}/main"

        compiler_args = [
            "-fPIC",
            "-std=c++20",
            main_cpp_path,
            self.output_file,
            "-o",
            executable_path,
        ]

        # Add any additional compiler flags or include paths as needed
        # compiler_args.append("-I/path/to/include")

        compiler_cmd = linker_path + " " + string_join(compiler_args, " ")

        print("ARX[INFO]: ", compiler_cmd)
        compile_result = system(compiler_cmd)

        ArxFile.delete_file(main_cpp_path)

        if compile_result != 0:
            llvm.errs() << "failed to compile and link object file"
            exit(1)

        return 0

    def open_interactive(self) -> int:
        """
        Open the Arx shell.

        Returns:
            int: The compilation result.
        """
        # Prime the first token.
        print(f"Arx {ARX_VERSION} \n")
        print(">>> ")

        while True:
            try:
                code = input()
                self.generate(Parser.parse())
            except KeyboardInterrupt:
                break
