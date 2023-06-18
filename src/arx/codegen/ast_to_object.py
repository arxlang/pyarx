import logging
import os
import sys
from typing import List, Any, Dict

from llvmlite import binding as llvm

from arx import ast
from arx.ast import Visitor

from arx.codegen.base import CodeGenBase
from arx.codegen.arx_llvm import ArxLLVM
from arx.logs import LogErrorV
from arx.io import ArxFile
from arx.lexer import Lexer
from arx.parser import Parser

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
    function_protos: Dict[str, ast.PrototypeAST]

    def __init__(self):
        self.function_protos: Dict[str, ast.PrototypeAST] = {}

    def get_function(self, name: str):
        """
        Put the function defined by the given name to result_func.

        Args:
            name: Function name
        """
        if name in ArxLLVM.module.globals:
            fn = ArxLLVM.module.get_global(name)
            return fn

        if name in self.function_protos:
            return self.function_protos[name].accept(self)

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

    def visit_tree(self, tree: ast.TreeAST) -> List[Any]:
        """
        The main loop that walks the AST.
        top ::= definition | external | expression | ';'

        Args:
            tree: The ast.TreeAST instance.
        """
        result = []
        for node in tree.nodes:
            result.append(node.accept(self))
        return result

    def visit_float_expr(self, expr: ast.FloatExprAST) -> llvm.ir.Value:
        """
        Code generation for ast.FloatExprAST.

        Args:
            expr: The ast.FloatExprAST instance
        """
        return llvm.ir.Constant(ArxLLVM.FLOAT_TYPE, expr.value)

    def visit_variable_expr(self, expr: ast.VariableExprAST) -> llvm.ir.Value:
        """
        Code generation for ast.VariableExprAST.

        Args:
            expr: The ast.VariableExprAST instance
        """
        expr_var = ArxLLVM.named_values.get(expr.name)

        if not expr_var:
            msg = f"Unknown variable name: {expr.name}"
            LogErrorV(msg)
            return

        return ArxLLVM.ir_builder.load(expr_var, expr.name)

    def visit_unary_expr(self, expr: ast.UnaryExprAST) -> llvm.ir.Value:
        """
        Code generation for ast.UnaryExprAST.

        Args:
            expr: The ast.UnaryExprAST instance
        """
        operand_value = expr.operand.accept(self)
        if not operand_value:
            return

        fn = self.get_function("unary" + expr.op_code)
        if not fn:
            LogErrorV("Unknown unary operator")
            return

        return ArxLLVM.ir_builder.call(fn, operand_value, "unop")

    def visit_binary_expr(self, expr: ast.BinaryExprAST) -> llvm.ir.Value:
        """
        Code generation for ast.BinaryExprAST.

        Args:
            expr: The ast.BinaryExprAST instance
        """
        if expr.op == "=":
            # Special case '=' because we don't want to emit the lhs as an expression.
            # Assignment requires the lhs to be an identifier.
            # This assumes we're building without RTTI because LLVM builds that way by default.
            # If you build LLVM with RTTI, this can be changed to a dynamic_cast for automatic error checking.
            var_lhs = expr.lhs

            if not isinstance(var_lhs, ast.VariableExprAST):
                LogErrorV("destination of '=' must be a variable")
                return

            # Codegen the rhs.
            val = expr.rhs.accept(self)

            if not val:
                return

            # Look up the name.
            variable = ArxLLVM.named_values[var_lhs.get_name()]

            if not variable:
                LogErrorV("Unknown variable name")
                return

            ArxLLVM.ir_builder.store(val, variable)
            return val

        llvm_lhs = expr.lhs.accept(self)
        llvm_rhs = expr.rhs.accept(self)

        if not llvm_lhs or not llvm_rhs:
            return

        if expr.op == "+":
            return ArxLLVM.ir_builder.fadd(llvm_lhs, llvm_rhs, "addtmp")
        elif expr.op == "-":
            return ArxLLVM.ir_builder.fsub(llvm_lhs, llvm_rhs, "subtmp")
        elif expr.op == "*":
            return ArxLLVM.ir_builder.fmull(llvm_lhs, llvm_rhs, "multmp")
        elif expr.op == "<":
            cmp_result = ArxLLVM.fcmp_unordered("<", lhs, rhs, "lttmp")
            # Convert bool 0/1 to float 0.0 or 1.0
            return ArxLLVM.ir_builder.uitofp(
                cmp_result, ArxLLVM.FLOAT_TYPE, "booltmp"
            )
        elif expr.op == ">":
            cmp_result = ArxLLVM.fcmp_unordered(">", lhs, rhs, "gttmp")
            # Convert bool 0/1 to float 0.0 or 1.0
            return ArxLLVM.ir_builder.uitofp(
                cmp_result, ArxLLVM.FLOAT_TYPE, "booltmp"
            )

        # If it wasn't a builtin binary operator, it must be a user defined one. Emit a call to it.
        fn = self.get_function("binary" + expr.op)
        return ArxLLVM.ir_builder.call(fn, [llvm_lhs, llvm_rhs], "binop")

    def visit_call_expr(self, expr: ast.CallExprAST) -> llvm.ir.Value:
        """
        Code generation for ast.CallExprAST.

        Args:
            expr: The ast.CallExprAST instance
        """
        callee_f = self.get_function(expr.callee)

        if not callee_f:
            LogErrorV("Unknown function referenced")
            return

        if callee_f.arg_size() != len(expr.args):
            LogErrorV("Incorrect # arguments passed")
            return

        args_v = []
        for arg in expr.args:
            args_v_item = arg.accept(self)
            if not args_v_item:
                return
            args_v.append(args_v_item)

        return ArxLLVM.ir_builder.call(callee_f, args_v, "calltmp")

    def visit_if_expr(self, expr: ast.IfExprAST) -> llvm.ir.Value:
        """
        Code generation for ast.IfExprAST.

        Args:
            expr: The ast.IfExprAST instance
        """
        cond_v = expr.cond.accept(self)

        if not cond_v:
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

        then_v = expr.then.accept(self)

        if not then_v:
            return

        ArxLLVM.ir_builder.CreateBr(merge_bb)
        # Codegen of 'then' can change the current block, update then_bb for the PHI.
        then_bb = ArxLLVM.ir_builder.GetInsertBlock()

        # Emit else block.
        fn.getBasicBlockList().push_back(else_bb)
        ArxLLVM.ir_builder.SetInsertPoint(else_bb)

        else_v = expr.else_.accept(self)
        if not else_v:
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

        return pn

    def visit_for_expr(self, expr: ast.ForExprAST) -> llvm.ir.Value:
        """
        Code generation for ast.ForExprAST.

        Args:
            expr: The ast.ForExprAST instance.
        """
        fn = ArxLLVM.ir_builder.GetInsertBlock().getParent()

        # Create an alloca for the variable in the entry block.
        # TODO: maybe it would be safe to change it to void
        alloca = self.create_entry_block_alloca(fn, expr.var_name, "float")

        # Emit the start code first, without 'variable' in scope.
        start_val = expr.start.accept(self)
        if not start_val:
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
        body_val = expr.body.accept(self)

        if not body_val:
            return

        # Emit the step value.
        step_val = None
        if expr.step:
            step_val = expr.step.accept(self)
            if not step_val:
                return
        else:
            # If not specified, use 1.0.
            step_val = llvm.ir.Constant(ArxLLVM.FLOAT_TYPE, 1.0)

        # Compute the end condition.
        end_cond = expr.end.accept(self)
        if not end_cond:
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
        return llvm.ir.Constant.getNullValue(ArxLLVM.FLOAT_TYPE)

    def visit_var_expr(self, expr: ast.VarExprAST) -> llvm.ir.Value:
        """
        Code generation for ast.VarExprAST.

        Args:
            expr: The ast.VarExprAST instance.
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

            init_val: llvm.ir.Value
            if init:
                init_val = init.accept(self)
                if not init_val:
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
        body_val = expr.body.accept(self)
        if not body_val:
            return

        # Pop all our variables from scope.
        for i, (var_name, _) in enumerate(expr.var_names.items()):
            ArxLLVM.named_values[var_name] = old_bindings[i]

        # Return the body computation.
        return body_val

    def visit_prototype(self, expr: ast.PrototypeAST) -> llvm.ir.Function:
        """
        Code generation for PrototypeExprAST.

        Args:
            expr: The ast.PrototypeAST instance.
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

        return fn

    def visit_function(self, expr: ast.FunctionAST) -> llvm.ir.Function:
        """
        Code generation for FunctionExprAST.

        Transfer ownership of the prototype to the ArxLLVM::function_protos map,
        but keep a reference to it for use below.

        Args:
            expr: The ast.FunctionAST instance.
        """
        proto = expr.proto
        self.function_protos[expr.proto.get_name()] = expr.proto
        fn = self.get_function(proto.get_name())

        if not fn:
            return

        # Create a new basic block to start insertion into.
        basic_block = fn.append_basic_block("entry")

        # Record the function arguments in the named_values map.
        ArxLLVM.named_values.clear()

        self.ir_builder = llvm.ir.IRBuilder(basic_block)

        for llvm_arg in fn.args:
            # Create an alloca for this variable.
            alloca = self.ir_builder.alloca(
                ArxLLVM.FLOAT_TYPE, llvm_arg._get_name()
            )

            # Store the initial value into the alloca.
            self.ir_builder.store(llvm_arg, alloca)

            # Add arguments to variable symbol table.
            ArxLLVM.named_values[str(llvm_arg._get_name())] = alloca

        retval = expr.body.accept(self)

        # Validate the generated code, checking for consistency.
        if retval:
            self.ir_builder.ret(retval)

        else:
            self.ir_builder.ret(llvm.ir.Constant(ArxLLVM.FLOAT_TYPE, 0))
        return fn

    def visit_return_expr(self, expr: ast.ReturnExprAST) -> llvm.ir.Value:
        """
        Code generation for ast.ReturnExprAST.

        Args:
            expr: The ast.ReturnExprAST instance.
        """
        # llvm_return_val = self.result_val
        #
        # if llvm_return_val:
        #     ArxLLVM.ir_builder.CreateRet(llvm_return_val)
        return


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

    def evaluate(self, tree_ast: ast.TreeAST) -> int:
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
