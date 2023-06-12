from typing import List

from deps import *


class ASTToOutputVisitor(Visitor, shared_from_this=True):
    def __init__(self):
        self.indent: int = 0
        self.annotation: str = ""

    def indentation(self) -> str:
        """
        Get the string representing the current indentation level.

        Returns:
            The string representing the current indentation level.
        """
        return " " * self.indent

    def set_annotation(self, annotation: str) -> None:
        """
        Set the annotation for the visitor.

        Args:
            annotation: The annotation to set.
        """
        self.annotation = annotation

    def get_annotation(self) -> str:
        """
        Get the current annotation and reset it.

        Returns:
            The current annotation.
        """
        annotation = self.annotation
        self.annotation = ""
        return annotation

    def visit(self, expr: FloatExprAST) -> None:
        """
        Visit a FloatExprAST node.

        Args:
            expr: The FloatExprAST node to visit.
        """
        print(
            f"{self.indentation()}{self.get_annotation()}(Number {expr.val})"
        )

    def visit(self, expr: VariableExprAST) -> None:
        """
        Visit a VariableExprAST node.

        Args:
            expr: The VariableExprAST node to visit.
        """
        print(
            f"{self.indentation()}{self.get_annotation()}(VariableExprAST {expr.name})"
        )

    def visit(self, expr: UnaryExprAST) -> None:
        """
        Visit a UnaryExprAST node.

        Args:
            expr: The UnaryExprAST node to visit.
        """
        print("(UnaryExprAST)")

    def visit(self, expr: BinaryExprAST) -> None:
        """
        Visit a BinaryExprAST node.

        Args:
            expr: The BinaryExprAST node to visit.
        """
        print(f"{self.indentation()}{self.get_annotation()}(")
        self.indent += INDENT_SIZE

        print(f"{self.indentation()}BinaryExprAST (")
        self.indent += INDENT_SIZE

        expr.lhs.accept(self)
        print(", ")

        print(f"{self.indentation()}(OP {expr.op}),")

        expr.rhs.accept(self)
        print(self.indentation())

        self.indent -= INDENT_SIZE
        print(f"{self.indentation()})")

        self.indent -= INDENT_SIZE
        print(f"{self.indentation()})")

    def visit(self, expr: CallExprAST) -> None:
        """
        Visit a CallExprAST node.

        Args:
            expr: The CallExprAST node to visit.
        """
        print(f"{self.indentation()}{self.get_annotation()}(")
        self.indent += INDENT_SIZE

        print(f"{self.indentation()}CallExprAST {expr.callee}(")
        self.indent += INDENT_SIZE

        for node in expr.args:
            node.get().accept(self)
            print()

        self.indent -= INDENT_SIZE
        print(f"{self.indentation()})")

        self.indent -= INDENT_SIZE
        print(f"{self.indentation()})")

    def visit(self, expr: IfExprAST) -> None:
        """
        Visit an IfExprAST node.

        Args:
            expr: The IfExprAST node to visit.
        """
        print(f"{self.indentation()}(")
        self.indent += INDENT_SIZE

        print(f"{self.indentation()}IfExprAST (")
        self.indent += INDENT_SIZE
        self.set_annotation("<COND>")

        expr.cond.accept(self)
        print(",")
        self.set_annotation("<THEN>")

        expr.then.accept(self)

        if expr.else_:
            print(",")
            self.set_annotation("<ELSE>")
            expr.else_.accept(self)
            print()
        else:
            print()
            print(f"{self.indentation()}()")

        self.indent -= INDENT_SIZE
        print(f"{self.indentation()})")

        self.indent -= INDENT_SIZE
        print(f"{self.indentation()})")

    def visit(self, expr: ForExprAST) -> None:
        """
        Visit a ForExprAST node.

        Args:
            expr: The ForExprAST node to visit.
        """
        print(f"{self.indentation()}{self.get_annotation()}(")
        self.indent += INDENT_SIZE

        print(f"{self.indentation()}ForExprAST (")
        self.indent += INDENT_SIZE

        self.set_annotation("<START>")
        expr.start.accept(self)
        print(", ")

        self.set_annotation("<END>")
        expr.end.accept(self)
        print(", ")

        self.set_annotation("<STEP>")
        expr.step.accept(self)
        print(", ")

        self.set_annotation("<BODY>")
        expr.body.accept(self)
        print()

        self.indent -= INDENT_SIZE
        print(f"{self.indentation()})")

        self.indent -= INDENT_SIZE
        print(f"{self.indentation()})")

    def visit(self, expr: VarExprAST) -> None:
        """
        Visit a VarExprAST node.

        Args:
            expr: The VarExprAST node to visit.
        """
        print("(VarExprAST ")
        self.indent += INDENT_SIZE

        for var_expr in expr.var_names:
            var_expr.second.accept(self)
            print(",")

        self.indent -= INDENT_SIZE

        print(")")

    def visit(self, expr: PrototypeAST) -> None:
        """
        Visit a PrototypeAST node.

        Args:
            expr: The PrototypeAST node to visit.
        """
        print(f"(PrototypeAST {expr.name})")

    def visit(self, expr: FunctionAST) -> None:
        """
        Visit a FunctionAST node.

        Args:
            expr: The FunctionAST node to visit.
        """
        print(f"{self.indentation()}(")
        self.indent += INDENT_SIZE

        print(f"{self.indentation()}Function {expr.proto.name} <ARGS> (")
        self.indent += INDENT_SIZE

        for node in expr.proto.args:
            node.accept(self)
            print(",")

        self.indent -= INDENT_SIZE
        print(f"{self.indentation()}),")
        print(f"{self.indentation()}<BODY> (")

        self.indent += INDENT_SIZE
        expr.body.accept(self)

        self.indent -= INDENT_SIZE
        print()
        print(f"{self.indentation()}),")

        self.indent -= INDENT_SIZE
        print(f"{self.indentation()})")

    def visit(self, expr: ReturnExprAST) -> None:
        """
        Visit a ReturnExprAST node.

        Args:
            expr: The ReturnExprAST node to visit.
        """
        print(f"(ReturnExprAST {self.visit(expr)})")


def print_ast(ast: TreeAST) -> int:
    visitor_print = ASTToOutputVisitor()

    print("[")
    visitor_print.indent += INDENT_SIZE

    for node in ast.nodes:
        node.accept(visitor_print)
        print(f"{visitor_print.indentation()},")

    print("]")
    return 0
