from typing import List, Optional

import llvm

from arx.ast import (
    BinaryExprAST,
    CallExprAST,
    FloatExprAST,
    ForExprAST,
    FunctionAST,
    IfExprAST,
    PrototypeAST,
    UnaryExprAST,
    VarExprAST,
    VariableExprAST,
)
from arx.codegen.ast_to_object import ObjectGeneratorVisitor


class ASTToLLVMIRVisitor(ObjectGeneratorVisitor):
    def __init__(self):
        super().__init__()
        self.llvm_di_compile_unit: Optional[llvm.DICompileUnit] = None
        self.llvm_di_lexical_blocks: List[llvm.DIScope] = []
        self.exit_on_err = llvm.ExitOnError()

    def visit_float_expr(self, expr: FloatExprAST) -> None:
        """
        Code generation for FloatExprAST.

        Args:
            expr (FloatExprAST): The FloatExprAST.

        Returns:
            None
        """
        self.emit_location(expr)
        ObjectGeneratorVisitor.visit(expr)

    def visit_variable_expr(self, expr: VariableExprAST) -> None:
        """
        Code generation for VariableExprAST.

        Args:
            expr (VariableExprAST): The VariableExprAST.

        Returns:
            None
        """
        self.emit_location(expr)
        ObjectGeneratorVisitor.visit(expr)

    def visit_unary_expr(self, expr: UnaryExprAST) -> None:
        """
        Code generation for UnaryExprAST.

        Args:
            expr (UnaryExprAST): The UnaryExprAST.

        Returns:
            None
        """
        self.emit_location(expr)
        ObjectGeneratorVisitor.visit(expr)

    def visit_binary_expr(self, expr: BinaryExprAST) -> None:
        """
        Code generation for BinaryExprAST.

        Args:
            expr (BinaryExprAST): The BinaryExprAST.

        Returns:
            None
        """
        self.emit_location(expr)
        ObjectGeneratorVisitor.visit(expr)

    def visit_call_expr(self, expr: CallExprAST) -> None:
        """
        Code generation for CallExprAST.

        Args:
            expr (CallExprAST): The CallExprAST.

        Returns:
            None
        """
        self.emit_location(expr)
        ObjectGeneratorVisitor.visit(expr)

    def visit_if_expr(self, expr: IfExprAST) -> None:
        """
        Code generation for IfExprAST.

        Args:
            expr (IfExprAST): The IfExprAST.

        Returns:
            None
        """
        self.emit_location(expr)
        ObjectGeneratorVisitor.visit(expr)

    def visit_for_expr(self, expr: ForExprAST) -> None:
        """
        Code generation for ForExprAST.

        Args:
            expr (ForExprAST): The ForExprAST.

        Returns:
            None
        """
        self.emit_location(expr)
        ObjectGeneratorVisitor.visit(expr)

    def visit_var_expr(self, expr: VarExprAST) -> None:
        """
        Code generation for VarExprAST.

        Args:
            expr (VarExprAST): The VarExprAST.

        Returns:
            None
        """
        self.emit_location(expr)
        ObjectGeneratorVisitor.visit(expr)

    def visit_prototype_expr(self, expr: PrototypeAST) -> None:
        """
        Code generation for PrototypeExprAST.

        Args:
            expr (PrototypeAST): The PrototypeAST.

        Returns:
            None
        """
        ObjectGeneratorVisitor.visit(expr)

    def visit_function(self, expr: FunctionAST) -> None:
        """
        Code generation for FunctionExprAST.

        Transfer ownership of the prototype to the ArxLLVM::function_protos map,
        but keep a reference to it for use below.

        Args:
            expr (FunctionAST): The FunctionAST.

        Returns:
            None
        """
        proto = expr.proto
        self.function_protos[proto.get_name()] = expr.proto
        self.get_function(proto.get_name())
        fn = self.result_func

        if not fn:
            self.result_func = None
            return

        # Create a new basic block to start insertion into.
        basic_block = llvm.BasicBlock.Create(ArxLLVM.context, "entry", fn)
        ArxLLVM.ir_builder.SetInsertPoint(basic_block)

        # Create a subprogram DIE for this function.
        di_unit = ArxLLVM.di_builder.createFile(
            self.llvm_di_compile_unit.getFilename(),
            self.llvm_di_compile_unit.getDirectory(),
        )
        file_context = di_unit
        line_no = proto.get_line()
        ScopeLine = line_no
        di_subprogram = ArxLLVM.di_builder.createFunction(
            file_context,
            proto.get_name(),
            llvm.StringRef(),
            di_unit,
            line_no,
            self.CreateFunctionType(fn.arg_size()),
            ScopeLine,
            llvm.DINode.FlagPrototyped,
            llvm.DISubprogram.SPFlagDefinition,
        )
        fn.setSubprogram(di_subprogram)

        # Push the current scope.
        self.llvm_di_lexical_blocks.append(di_subprogram)

        # Unset the location for the prologue emission (leading instructions with no
        # location in a function are considered part of the prologue and the
        # debugger will run past them when breaking on a function)
        null_ast = ExprAST()
        self.emit_location(null_ast)

        # Record the function arguments in the named_values map.
        ArxLLVM.named_values.clear()
        arg_idx = 0
        for llvm_arg in fn.args():
            # Create an alloca for this variable.
            alloca = self.create_entry_block_alloca(
                fn, llvm_arg.getName(), "float"
            )

            # Create a debug descriptor for the variable.
            di_local_variable = ArxLLVM.di_builder.createParameterVariable(
                di_subprogram,
                llvm_arg.getName(),
                arg_idx + 1,
                di_unit,
                line_no,
                ArxLLVM.DI_FLOAT_TYPE,
                True,
            )
            ArxLLVM.di_builder.insertDeclare(
                alloca,
                di_local_variable,
                ArxLLVM.di_builder.createExpression(),
                llvm.DILocation.get(
                    di_subprogram.getContext(), line_no, 0, di_subprogram
                ),
                ArxLLVM.ir_builder.GetInsertBlock(),
            )

            # Store the initial value into the alloca.
            ArxLLVM.ir_builder.CreateStore(llvm_arg, alloca)

            # Add arguments to variable symbol table.
            ArxLLVM.named_values[str(llvm_arg.getName())] = alloca

        self.emit_location(expr.body)

        expr.body.accept(self)
        llvm_return_val = self.result_val

        if llvm_return_val:
            # Finish off the function.
            ArxLLVM.ir_builder.CreateRet(llvm_return_val)

            # Pop off the lexical block for the function.
            self.llvm_di_lexical_blocks.pop()

            # Validate the generated code, checking for consistency.
            llvm.verifyFunction(fn)

            self.result_func = fn
            return

        # Error reading body, remove function.
        fn.eraseFromParent()

        self.result_func = None

        # Pop off the lexical block for the function since we added it unconditionally.
        self.llvm_di_lexical_blocks.pop()

    def initialize(self) -> None:
        """
        Initialize LLVM Module And PassManager.
        """
        ArxLLVM.initialize()

    def CreateFunctionType(self, num_args: int) -> llvm.DISubroutineType:
        """
        Create a function type with the given number of arguments.

        Args:
            num_args (int): The number of arguments.

        Returns:
            llvm.DISubroutineType: The created function type.
        """
        elty_tys: List[llvm.Metadata] = []

        # Add the result type.
        elty_tys.append(ArxLLVM.DI_FLOAT_TYPE)

        for i in range(num_args):
            elty_tys.append(ArxLLVM.DI_FLOAT_TYPE)

        return ArxLLVM.di_builder.createSubroutineType(
            ArxLLVM.di_builder.getOrCreateTypeArray(elty_tys)
        )

    def emit_location(self, ast: ExprAST) -> None:
        """
        Emit the location information for the given AST expression.

        Args:
            ast (ExprAST): The AST expression.

        Returns:
            None
        """
        if not ast:
            return ArxLLVM.ir_builder.SetCurrentDebugLocation(llvm.DebugLoc())

        di_scope = (
            llvm_di_compile_unit
            if self.llvm_di_lexical_blocks.empty()
            else self.llvm_di_lexical_blocks.back()
        )

        ArxLLVM.ir_builder.SetCurrentDebugLocation(
            llvm.DILocation.get(
                di_scope.getContext(), ast.get_line(), ast.get_col(), di_scope
            )
        )


def compile_llvm_ir(ast: TreeAST) -> int:
    """
    Compile an AST to object file.

    Parameters:
    -----------
        ast (TreeAST): The AST tree object.

    Returns:
    --------
        int: The result of the compilation.
    """
    codegen = ASTToLLVMIRVisitor()

    Lexer.get_next_token()

    codegen.initialize()

    LOG(INFO) << "Starting main_loop"

    codegen.llvm_di_compile_unit = ArxLLVM.di_builder.createCompileUnit(
        llvm.dwarf.DW_LANG_C,
        ArxLLVM.di_builder.createFile("fib.ks", "."),
        "Arx Compiler",
        False,
        "",
        0,
    )

    LOG(INFO) << "initialize Target"

    ArxLLVM.module.addModuleFlag(
        llvm.Module.Warning, "Debug Info Version", llvm.DEBUG_METADATA_VERSION
    )

    if llvm.Triple(llvm.sys.getProcessTriple()).isOSDarwin():
        ArxLLVM.module.addModuleFlag(llvm.Module.Warning, "Dwarf Version", 2)

    ArxLLVM.di_builder = llvm.DIBuilder(ArxLLVM.module)

    codegen.llvm_di_compile_unit = ArxLLVM.di_builder.createCompileUnit(
        llvm.dwarf.DW_LANG_C,
        ArxLLVM.di_builder.createFile("fib.arxks", "."),
        "Arx Compiler",
        False,
        "",
        0,
    )

    codegen.visit_tree(ast)

    ArxLLVM.di_builder.finalize()
    ArxLLVM.module.print(llvm.errs(), None)

    return 0


def open_shell_llvm_ir() -> int:
    """
    Open the Arx shell.

    Returns:
        int: The result of the shell opening.
    """
    stderr.write("Arx {}\n".format(ARX_VERSION))
    stderr.write(">>> ")

    ast = TreeAST()
    return compile_llvm_ir(ast)
