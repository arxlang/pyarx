"""Set of classes and functions to emit the AST from a given source code."""
from arx.codegen.base import CodeGenBase, CodeGenResultType
from arx import ast
from arx.parser import INDENT_SIZE


class ASTtoOutput(CodeGenBase):
    """Show the AST for the given source code."""

    def __init__(self) -> None:
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

    def set_annotation(self, annotation: str) -> None:
        """
        Set the annotation for the visitor.

        Parameters
        ----------
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

    def visit_block(self, expr: ast.BlockAST) -> CodeGenResultType:
        """
        Visit method for tree ast.

        Parameters
        ----------
            expr: The ast.BlockAST node to visit.
        """
        for node in expr.nodes:
            self.visit(node)
        return None

    def visit_float_expr(self, expr: ast.FloatExprAST) -> CodeGenResultType:
        """
        Visit a ast.FloatExprAST node.

        Parameters
        ----------
            expr: The ast.FloatExprAST node to visit.
        """
        print(
            f"{self.indentation()}{self.get_annotation()}(Number {expr.value})"
        )
        return None

    def visit_variable_expr(
        self, expr: ast.VariableExprAST
    ) -> CodeGenResultType:
        """
        Visit a ast.VariableExprAST node.

        Parameters
        ----------
            expr: The ast.VariableExprAST node to visit.
        """
        print(
            f"{self.indentation()}{self.get_annotation()}"
            f"(ast.VariableExprAST {expr.name})"
        )
        return None

    def visit_unary_expr(self, expr: ast.UnaryExprAST) -> CodeGenResultType:
        """
        Visit a ast.UnaryExprAST node.

        Parameters
        ----------
            expr: The ast.UnaryExprAST node to visit.
        """
        print("(ast.UnaryExprAST)")
        return None

    def visit_binary_expr(self, expr: ast.BinaryExprAST) -> CodeGenResultType:
        """
        Visit a ast.BinaryExprAST node.

        Parameters
        ----------
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
        return None

    def visit_call_expr(self, expr: ast.CallExprAST) -> CodeGenResultType:
        """
        Visit a ast.CallExprAST node.

        Parameters
        ----------
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
        return None

    def visit_if_expr(self, expr: ast.IfStmtAST) -> CodeGenResultType:
        """
        Visit an ast.IfStmtAST node.

        Parameters
        ----------
            expr: The ast.IfStmtAST node to visit.
        """
        print(f"{self.indentation()}(")
        self.indent += INDENT_SIZE

        print(f"{self.indentation()}ast.IfStmtAST (")
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
        return None

    def visit_for_expr(self, expr: ast.ForStmtAST) -> CodeGenResultType:
        """
        Visit a ast.ForStmtAST node.

        Parameters
        ----------
            expr: The ast.ForStmtAST node to visit.
        """
        print(f"{self.indentation()}{self.get_annotation()}(")
        self.indent += INDENT_SIZE

        print(f"{self.indentation()}ast.ForStmtAST (")
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
        return None

    def visit_var_expr(self, expr: ast.VarExprAST) -> CodeGenResultType:
        """
        Visit a ast.VarExprAST node.

        Parameters
        ----------
            expr: The ast.VarExprAST node to visit.
        """
        print("(ast.VarExprAST ")
        self.indent += INDENT_SIZE

        for var_expr in expr.var_names:
            self.visit(var_expr[1])
            print(",")

        self.indent -= INDENT_SIZE

        print(")")
        return None

    def visit_prototype(self, expr: ast.PrototypeAST) -> CodeGenResultType:
        """
        Visit a ast.PrototypeAST node.

        Parameters
        ----------
            expr: The ast.PrototypeAST node to visit.
        """
        print(f"(ast.PrototypeAST {expr.name})")
        return None

    def visit_function(self, expr: ast.FunctionAST) -> CodeGenResultType:
        """
        Visit a ast.FunctionAST node.

        Parameters
        ----------
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
        return None

    def visit_return_expr(self, expr: ast.ReturnStmtAST) -> CodeGenResultType:
        """
        Visit a ast.ReturnStmtAST node.

        Parameters
        ----------
            expr: The ast.ReturnStmtAST node to visit.
        """
        print(f"(ast.ReturnStmtAST {self.visit(expr.value)})")
        return None

    def emit_ast(self, ast: ast.BlockAST) -> None:
        """Print the AST for the given source code."""
        print("[")
        self.indent += INDENT_SIZE

        for node in ast.nodes:
            if not node:
                continue
            self.visit(node)
            print(f"{self.indentation()},")

        print("]")
        return
