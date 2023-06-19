"""Set of classes and functions to emit the AST from a given source code."""
from arx.codegen.base import CodeGenBase
from arx import ast

INDENT_SIZE = 2


class ASTtoOutput(CodeGenBase):
    """Show the AST for the given source code."""

    def __init__(self):
        self.indent: int = 0
        self.annotation: str = ""

    def indentation(self) -> str:
        """
        Get the string representing the current indentation level.

        Returns
        -------
            The string representing the current indentation level.
        """
        return " " * self.indent

    def set_annotation(self, annotation: str):
        """
        Set the annotation for the visitor.

        Args:
            annotation: The annotation to set.
        """
        self.annotation = annotation

    def get_annotation(self) -> str:
        """
        Get the current annotation and reset it.

        Returns
        -------
            The current annotation.
        """
        annotation = self.annotation
        self.annotation = ""
        return annotation

    def visit_float_expr(self, expr: ast.FloatExprAST):
        """
        Visit a ast.FloatExprAST node.

        Args:
            expr: The ast.FloatExprAST node to visit.
        """
        print(
            f"{self.indentation()}{self.get_annotation()}(Number {expr.value})"
        )

    def visit_variable_expr(self, expr: ast.VariableExprAST):
        """
        Visit a ast.VariableExprAST node.

        Args:
            expr: The ast.VariableExprAST node to visit.
        """
        print(
            f"{self.indentation()}{self.get_annotation()}"
            f"(ast.VariableExprAST {expr.name})"
        )

    def visit_unary_expr(self, expr: ast.UnaryExprAST):
        """
        Visit a ast.UnaryExprAST node.

        Args:
            expr: The ast.UnaryExprAST node to visit.
        """
        print("(ast.UnaryExprAST)")

    def visit_binary_expr(self, expr: ast.BinaryExprAST):
        """
        Visit a ast.BinaryExprAST node.

        Args:
            expr: The ast.BinaryExprAST node to visit.
        """
        print(f"{self.indentation()}{self.get_annotation()}(")
        self.indent += INDENT_SIZE

        print(f"{self.indentation()}ast.BinaryExprAST (")
        self.indent += INDENT_SIZE

        self.visit(expr.lhs)
        print(", ")

        print(f"{self.indentation()}(OP {expr.op}),")

        self.visit(expr.rhs)
        print(self.indentation())

        self.indent -= INDENT_SIZE
        print(f"{self.indentation()})")

        self.indent -= INDENT_SIZE
        print(f"{self.indentation()})")

    def visit_call_expr(self, expr: ast.CallExprAST):
        """
        Visit a ast.CallExprAST node.

        Args:
            expr: The ast.CallExprAST node to visit.
        """
        print(f"{self.indentation()}{self.get_annotation()}(")
        self.indent += INDENT_SIZE

        print(f"{self.indentation()}ast.CallExprAST {expr.callee}(")
        self.indent += INDENT_SIZE

        for node in expr.args:
            self.visit(node)
            print()

        self.indent -= INDENT_SIZE
        print(f"{self.indentation()})")

        self.indent -= INDENT_SIZE
        print(f"{self.indentation()})")

    def visit_if_expr(self, expr: ast.IfExprAST):
        """
        Visit an ast.IfExprAST node.

        Args:
            expr: The ast.IfExprAST node to visit.
        """
        print(f"{self.indentation()}(")
        self.indent += INDENT_SIZE

        print(f"{self.indentation()}ast.IfExprAST (")
        self.indent += INDENT_SIZE
        self.set_annotation("<COND>")

        self.visit(expr.cond)
        print(",")
        self.set_annotation("<THEN>")

        self.visit(expr.then_)

        if expr.else_:
            print(",")
            self.set_annotation("<ELSE>")
            self.visit(expr.else_)
            print()
        else:
            print()
            print(f"{self.indentation()}()")

        self.indent -= INDENT_SIZE
        print(f"{self.indentation()})")

        self.indent -= INDENT_SIZE
        print(f"{self.indentation()})")

    def visit_for_expr(self, expr: ast.ForExprAST):
        """
        Visit a ast.ForExprAST node.

        Args:
            expr: The ast.ForExprAST node to visit.
        """
        print(f"{self.indentation()}{self.get_annotation()}(")
        self.indent += INDENT_SIZE

        print(f"{self.indentation()}ast.ForExprAST (")
        self.indent += INDENT_SIZE

        self.set_annotation("<START>")
        self.visit(expr.start)
        print(", ")

        self.set_annotation("<END>")
        self.visit(expr.end)
        print(", ")

        self.set_annotation("<STEP>")
        self.visit(expr.step)
        print(", ")

        self.set_annotation("<BODY>")
        self.visit(expr.body)
        print()

        self.indent -= INDENT_SIZE
        print(f"{self.indentation()})")

        self.indent -= INDENT_SIZE
        print(f"{self.indentation()})")

    def visit_var_expr(self, expr: ast.VarExprAST):
        """
        Visit a ast.VarExprAST node.

        Args:
            expr: The ast.VarExprAST node to visit.
        """
        print("(ast.VarExprAST ")
        self.indent += INDENT_SIZE

        for var_expr in expr.var_names:
            self.visit(var_expr.second)
            print(",")

        self.indent -= INDENT_SIZE

        print(")")

    def visit_prototype(self, expr: ast.PrototypeAST):
        """
        Visit a ast.PrototypeAST node.

        Args:
            expr: The ast.PrototypeAST node to visit.
        """
        print(f"(ast.PrototypeAST {expr.name})")

    def visit_function(self, expr: ast.FunctionAST):
        """
        Visit a ast.FunctionAST node.

        Args:
            expr: The ast.FunctionAST node to visit.
        """
        print(f"{self.indentation()}(")
        self.indent += INDENT_SIZE

        print(f"{self.indentation()}Function {expr.proto.name} <ARGS> (")
        self.indent += INDENT_SIZE

        for node in expr.proto.args:
            self.visit(node)
            print(",")

        self.indent -= INDENT_SIZE
        print(f"{self.indentation()}),")
        print(f"{self.indentation()}<BODY> (")

        self.indent += INDENT_SIZE
        self.visit(expr.body)

        self.indent -= INDENT_SIZE
        print()
        print(f"{self.indentation()}),")

        self.indent -= INDENT_SIZE
        print(f"{self.indentation()})")

    def visit_return_expr(self, expr: ast.ReturnExprAST):
        """
        Visit a ast.ReturnExprAST node.

        Args:
            expr: The ast.ReturnExprAST node to visit.
        """
        print(f"(ast.ReturnExprAST {self.visit(expr.expr)})")

    def emit_ast(self, ast: ast.TreeAST) -> int:
        """Print the AST for the given source code."""

        print("[")
        self.indent += INDENT_SIZE

        for node in ast.nodes:
            if not node:
                continue
            self.visit(node)
            print(f"{self.indentation()},")

        print("]")
