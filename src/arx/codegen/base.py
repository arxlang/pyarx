"""Base module for code generation."""
from typing import Any, Callable, Type, Dict

import llvmlite.binding as llvm

from arx import ast
from arx.exceptions import CodeGenException


class CodeGenBase:
    """A base Visitor pattern class."""

    def visit(self, expr: ast.ExprAST) -> Any:
        """Call the correspondent visit function for the given expr type."""
        map_visit_expr: Dict[Type[ast.ExprAST], Callable] = {
            ast.BinaryExprAST: self.visit_binary_expr,
            ast.CallExprAST: self.visit_call_expr,
            ast.FloatExprAST: self.visit_float_expr,
            ast.ForStmtAST: self.visit_for_expr,
            ast.FunctionAST: self.visit_function,
            ast.IfStmtAST: self.visit_if_expr,
            ast.PrototypeAST: self.visit_prototype,
            ast.ReturnStmtAST: self.visit_return_expr,
            ast.BlockAST: self.visit_block,
            ast.UnaryExprAST: self.visit_unary_expr,
            ast.VarExprAST: self.visit_var_expr,
            ast.VariableExprAST: self.visit_variable_expr,
        }

        fn = map_visit_expr.get(type(expr))

        if not fn:
            print("Fail to downcasting ExprAST.")
            return

        return fn(expr)

    def visit_binary_expr(self, expr: ast.BinaryExprAST) -> Any:
        """Visit method for binary expression."""
        raise CodeGenException("Not implemented yet.")

    def visit_call_expr(self, expr: ast.CallExprAST) -> Any:
        """Visit method for function call."""
        raise CodeGenException("Not implemented yet.")

    def visit_float_expr(self, expr: ast.FloatExprAST) -> Any:
        """Visit method for float."""
        raise CodeGenException("Not implemented yet.")

    def visit_for_expr(self, expr: ast.ForStmtAST) -> Any:
        """Visit method for `for` loop."""
        raise CodeGenException("Not implemented yet.")

    def visit_function(self, expr: ast.FunctionAST) -> Any:
        """Visit method for function definition."""
        raise CodeGenException("Not implemented yet.")

    def visit_if_expr(self, expr: ast.IfStmtAST) -> Any:
        """Visit method for if statement."""
        raise CodeGenException("Not implemented yet.")

    def visit_prototype(self, expr: ast.PrototypeAST) -> Any:
        """Visit method for prototype."""
        raise CodeGenException("Not implemented yet.")

    def visit_return_expr(self, expr: ast.ReturnStmtAST) -> Any:
        """Visit method for expression."""
        raise CodeGenException("Not implemented yet.")

    def visit_block(self, expr: ast.BlockAST) -> Any:
        """Visit method for tree ast."""
        raise CodeGenException("Not implemented yet.")

    def visit_unary_expr(self, expr: ast.UnaryExprAST) -> Any:
        """Visit method for unary expression."""
        raise CodeGenException("Not implemented yet.")

    def visit_var_expr(self, expr: ast.VarExprAST) -> Any:
        """Visit method for variable declaration."""
        raise CodeGenException("Not implemented yet.")

    def visit_variable_expr(self, expr: ast.VariableExprAST) -> Any:
        """Visit method for variable usage."""
        raise CodeGenException("Not implemented yet.")


class VariablesLLVM:
    """Store all the LLVM variables that is used for the code generation."""

    FLOAT_TYPE: llvm.ir.types.Type
    DOUBLE_TYPE: llvm.ir.types.Type
    INT8_TYPE: llvm.ir.types.Type
    INT32_TYPE: llvm.ir.types.Type
    VOID_TYPE: llvm.ir.types.Type

    context: llvm.ir.context.Context
    module: llvm.ir.module.Module

    ir_builder: llvm.ir.builder.IRBuilder

    def get_data_type(self, type_name: str) -> llvm.ir.types.Type:
        """
        Get the LLVM data type for the given type name.

        Parameters
        ----------
            type_name (str): The name of the type.

        Returns
        -------
            ir.Type: The LLVM data type.
        """
        if type_name == "float":
            return self.FLOAT_TYPE
        elif type_name == "double":
            return self.DOUBLE_TYPE
        elif type_name == "int8":
            return self.INT8_TYPE
        elif type_name == "int32":
            return self.INT32_TYPE
        elif type_name == "char":
            return self.INT8_TYPE
        elif type_name == "void":
            return self.VOID_TYPE

        raise CodeGenException("[EE] CodeGen(LLVM): type_name not valid.")


class CodeGenLLVMBase(CodeGenBase):
    """ArxLLVM gathers all the main global variables for LLVM workflow."""

    named_values: Dict[str, Any] = {}  # AllocaInst
    _llvm: VariablesLLVM

    def initialize(self):
        """Initialize self."""
        # self._llvm.context = llvm.ir.context.Context()
        self._llvm = VariablesLLVM()
        self._llvm.module = llvm.ir.module.Module("Arx")

        # initialize the target registry etc.
        llvm.initialize()
        llvm.initialize_all_asmprinters()
        llvm.initialize_all_targets()
        llvm.initialize_native_target()
        llvm.initialize_native_asmparser()
        llvm.initialize_native_asmprinter()

        # Create a new builder for the module.
        self._llvm.ir_builder = llvm.ir.IRBuilder()

        # Data Types
        self._llvm.FLOAT_TYPE = llvm.ir.FloatType()
        self._llvm.DOUBLE_TYPE = llvm.ir.DoubleType()
        self._llvm.INT8_TYPE = llvm.ir.IntType(8)
        self._llvm.INT32_TYPE = llvm.ir.IntType(32)
        self._llvm.VOID_TYPE = llvm.ir.VoidType()

    def evaluate(self, tree: ast.BlockAST):
        """Evaluate the given AST object."""
        raise CodeGenException(f"Not an evaluation for {tree} implement yet.")
