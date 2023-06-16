"""Set of classes and functions to emit the AST from a given source code."""
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

INDENT_SIZE = 2


class ASTToOutputVisitor(Visitor):
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

    def visit_float_expr(self, expr: FloatExprAST):
        """
        Visit a FloatExprAST node.

        Args:
            expr: The FloatExprAST node to visit.
        """
        print(
            f"{self.indentation()}{self.get_annotation()}(Number {expr.val})"
        )

    def visit_variable_expr(self, expr: VariableExprAST):
        """
        Visit a VariableExprAST node.

        Args:
            expr: The VariableExprAST node to visit.
        """
        print(
            f"{self.indentation()}{self.get_annotation()}"
            f"(VariableExprAST {expr.name})"
        )

    def visit_unary_expr(self, expr: UnaryExprAST):
        """
        Visit a UnaryExprAST node.

        Args:
            expr: The UnaryExprAST node to visit.
        """
        print("(UnaryExprAST)")

    def visit_binary_expr(self, expr: BinaryExprAST):
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

    def visit_call_expr(self, expr: CallExprAST):
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
            node.accept(self)
            print()

        self.indent -= INDENT_SIZE
        print(f"{self.indentation()})")

        self.indent -= INDENT_SIZE
        print(f"{self.indentation()})")

    def visit_if_expr(self, expr: IfExprAST):
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

    def visit_for_expr(self, expr: ForExprAST):
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

    def visit_var_expr(self, expr: VarExprAST):
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

    def visit_prototype(self, expr: PrototypeAST):
        """
        Visit a PrototypeAST node.

        Args:
            expr: The PrototypeAST node to visit.
        """
        print(f"(PrototypeAST {expr.name})")

    def visit_function(self, expr: FunctionAST):
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

    def visit_return_expr(self, expr: ReturnExprAST):
        """
        Visit a ReturnExprAST node.

        Args:
            expr: The ReturnExprAST node to visit.
        """
        print(f"(ReturnExprAST {self.visit(expr.expr)})")


def emit_ast(ast: TreeAST) -> int:
    """Print the AST for the given source code."""
    visitor_print = ASTToOutputVisitor()

    print("[")
    visitor_print.indent += INDENT_SIZE

    for node in ast.nodes:
        if not node:
            continue
        node.accept(visitor_print)
        print(f"{visitor_print.indentation()},")

    print("]")
    return 0
