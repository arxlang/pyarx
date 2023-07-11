"""Set of classes and functions to emit the AST from a given source code."""
from typing import Any, Dict, List, TypeAlias, Union

import yaml

from arx.codegen.base import CodeGenBase
from arx import ast

OutputValueAST: TypeAlias = Union[str, int, float, List[Any], Dict[str, Any]]


class ASTtoOutput(CodeGenBase):
    """Show the AST for the given source code."""

    result_stack: List[OutputValueAST]

    def __init__(self) -> None:
        self.result_stack: List[OutputValueAST] = []

    def visit_block(self, expr: ast.BlockAST) -> None:
        """
        Visit method for tree ast.

        Parameters
        ----------
            expr: The ast.BlockAST node to visit.
        """
        block_node = []

        for node in expr.nodes:
            self.visit(node)
            block_node.append(self.result_stack.pop())

        self.result_stack.append(block_node)

    def visit_float_expr(self, expr: ast.FloatExprAST) -> None:
        """
        Visit a ast.FloatExprAST node.

        Parameters
        ----------
            expr: The ast.FloatExprAST node to visit.
        """
        self.result_stack.append(f"FLOAT[{expr.value}]")

    def visit_variable_expr(self, expr: ast.VariableExprAST) -> None:
        """
        Visit a ast.VariableExprAST node.

        Parameters
        ----------
            expr: The ast.VariableExprAST node to visit.
        """
        self.result_stack.append(f"VARIABLE[{expr.name, expr.type_name}]")

    def visit_unary_expr(self, expr: ast.UnaryExprAST) -> None:
        """
        Visit a ast.UnaryExprAST node.

        Parameters
        ----------
            expr: The ast.UnaryExprAST node to visit.
        """
        self.visit(expr.operand)
        node = {f"UNARY[{expr.op_code}]": self.result_stack.pop()}
        self.result_stack.append(node)

    def visit_binary_expr(self, expr: ast.BinaryExprAST) -> None:
        """
        Visit a ast.BinaryExprAST node.

        Parameters
        ----------
            expr: The ast.BinaryExprAST node to visit.
        """
        self.visit(expr.lhs)
        lhs = self.result_stack.pop()

        self.visit(expr.rhs)
        rhs = self.result_stack.pop()

        node = {f"BINARY[{expr.op}]": {"lhs": lhs, "rhs": rhs}}
        self.result_stack.append(node)

    def visit_call_expr(self, expr: ast.CallExprAST) -> None:
        """
        Visit a ast.CallExprAST node.

        Parameters
        ----------
            expr: The ast.CallExprAST node to visit.
        """
        call_args = []

        for node in expr.args:
            self.visit(node)
            call_args.append(self.result_stack.pop())

        call_node = {f"CALL[{expr.callee}]": {"args": call_args}}
        self.result_stack.append(call_node)

    def visit_if_stmt(self, expr: ast.IfStmtAST) -> None:
        """
        Visit an ast.IfStmtAST node.

        Parameters
        ----------
            expr: The ast.IfStmtAST node to visit.
        """
        self.visit(expr.cond)
        if_condition = self.result_stack.pop()

        self.visit(expr.then_)
        if_then = self.result_stack.pop()

        if expr.else_:
            self.visit(expr.else_)
            if_else = self.result_stack.pop()
        else:
            if_else = []

        node = {
            "IF-STMT": {
                "CONDITION": if_condition,
                "THEN": if_then,
            }
        }

        if if_else:
            node["IF-STMT"]["ELSE"] = if_else

        self.result_stack.append(node)

    def visit_for_stmt(self, expr: ast.ForStmtAST) -> None:
        """
        Visit a ast.ForStmtAST node.

        Parameters
        ----------
            expr: The ast.ForStmtAST node to visit.
        """
        self.visit(expr.start)
        for_start = self.result_stack.pop()

        self.visit(expr.end)
        for_end = self.result_stack.pop()

        self.visit(expr.step)
        for_step = self.result_stack.pop()

        self.visit(expr.body)
        for_body = self.result_stack.pop()

        node = {
            "FOR-STMT": {
                "start": for_start,
                "end": for_end,
                "step": for_step,
                "body": for_body,
            }
        }
        self.result_stack.append(node)

    def visit_var_expr(self, expr: ast.VarExprAST) -> None:
        """
        Visit a ast.VarExprAST node.

        Parameters
        ----------
            expr: The ast.VarExprAST node to visit.
        """
        raise Exception("Variable declaration will be changed soon.")

    def visit_prototype(self, expr: ast.PrototypeAST) -> None:
        """
        Visit a ast.PrototypeAST node.

        Parameters
        ----------
            expr: The ast.PrototypeAST node to visit.
        """
        raise Exception("Visitor method not necessary")

    def visit_function(self, expr: ast.FunctionAST) -> None:
        """
        Visit a ast.FunctionAST node.

        Parameters
        ----------
            expr: The ast.FunctionAST node to visit.
        """
        fn_args = []
        for node in expr.proto.args:
            self.visit(node)
            fn_args.append(self.result_stack.pop())

        self.visit(expr.body)
        fn_body = self.result_stack.pop()

        fn = {}
        fn[f"FUNCTION[{expr.proto.name}]"] = {
            "args": fn_args,
            "body": fn_body,
        }

        self.result_stack.append(fn)

    def visit_return_stmt(self, expr: ast.ReturnStmtAST) -> None:
        """
        Visit a ast.ReturnStmtAST node.

        Parameters
        ----------
            expr: The ast.ReturnStmtAST node to visit.
        """
        self.visit(expr.value)
        node = {"RETURN": self.result_stack.pop()}
        self.result_stack.append(node)

    def emit_ast(self, ast: ast.BlockAST) -> None:
        """Print the AST for the given source code."""
        self.visit_block(ast)

        tree_ast = {
            "ROOT": [
                {"MODULE[main]": self.result_stack.pop()},
            ]
        }
        print(yaml.dump(tree_ast, sort_keys=False))
