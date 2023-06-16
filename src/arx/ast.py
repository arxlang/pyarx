"""AST classes and functions."""
from enum import Enum
from typing import List, Tuple

from arx.lexer import Lexer, SourceLocation


class ExprKind(Enum):
    """The expression kind class used for downcasting."""

    GenericKind = -1

    # variables
    VariableKind = -10
    VarKind = -11  # var keyword for variable declaration

    # operators
    UnaryOpKind = -20
    BinaryOpKind = -21

    # functions
    PrototypeKind = -30
    FunctionKind = -31
    CallKind = -32
    ReturnKind = -33

    # control flow
    IfKind = -40
    ForKind = -41

    # data types
    NullDTKind = -100
    BooleanDTKind = -101
    Int8DTKind = -102
    UInt8DTKind = -103
    Int16DTKind = -104
    UInt16DTKind = -105
    Int32DTKind = -106
    UInt32DTKind = -107
    Int64DTKind = -108
    UInt64DTKind = -109
    FloatDTKind = -110
    DoubleDTKind = -111
    BinaryDTKind = -112
    StringDTKind = -113
    FixedSizeBinaryDTKind = -114
    Date32DTKind = -115
    Date64DTKind = -116
    TimestampDTKind = -117
    Time32DTKind = -118
    Time64DTKind = -119
    Decimal128DTKind = -120
    Decimal256DTKind = -121


class Visitor:
    """A base Visitor pattern class."""

    def visit(self, node: "ExprAST"):
        """Call the visit method for the given node object."""
        pass

    def clean(self):
        """Clean instance attributes."""
        pass


class ExprAST:
    loc: SourceLocation
    kind: "ExprAST"

    def __init__(self, loc: SourceLocation = Lexer.cur_loc):
        """Initialize the ExprAST instance."""
        self.kind = ExprKind.GenericKind
        self.loc = loc

    def get_line(self) -> int:
        """Return the line number for the expression occurrence."""
        return self.loc.line

    def get_col(self) -> int:
        """Return the column number for the expression occurrence."""
        return self.loc.col

    def accept(self, visitor: Visitor):
        """
        Invoke the appropriate visit method based on the expression kind.

        Parameters
        ----------
        visitor : Visitor
            The visitor object.

        Raises
        ------
        ValueError
            If the expression kind does not match any known type.
        """
        if self.kind == ExprKind.FloatDTKind:
            visitor.visit(self)
        elif self.kind == ExprKind.VariableKind:
            visitor.visit(self)
        elif self.kind == ExprKind.UnaryOpKind:
            visitor.visit(self)
        elif self.kind == ExprKind.BinaryOpKind:
            visitor.visit(self)
        elif self.kind == ExprKind.CallKind:
            visitor.visit(self)
        elif self.kind == ExprKind.IfKind:
            visitor.visit(self)
        elif self.kind == ExprKind.ForKind:
            visitor.visit(self)
        elif self.kind == ExprKind.VarKind:
            visitor.visit(self)
        elif self.kind == ExprKind.PrototypeKind:
            visitor.visit(self)
        elif self.kind == ExprKind.FunctionKind:
            visitor.visit(self)
        elif self.kind == ExprKind.ReturnKind:
            visitor.visit(self)
        elif self.kind == ExprKind.GenericKind:
            print("[WW] Generic Kind doesn't have a downcasting")
        else:
            print(self.kind)
            print("[WW] DOWNCASTING MATCH FAILED")
            visitor.clean()

    # def dump(self, out, ind: int):
    #     return out.write(f":{self.get_line()}:{self.get_col()}\n")


class FloatExprAST(ExprAST):
    """AST for the literal float number."""

    def __init__(self, val: float):
        """Initialize the FloatAST instance."""
        super().__init__()
        self.val = val
        self.kind = ExprKind.FloatDTKind

    # def dump(self, out, ind: int):
    #     return super().dump(out.write(str(self.val)), ind)


class VariableExprAST(ExprAST):
    """AST class for the variable usage."""

    def __init__(self, loc: SourceLocation, name: str, type_name: str):
        """Initialize the VariableExprAST instance."""
        super().__init__(loc)
        self.name = name
        self.type_name = type_name
        self.kind = ExprKind.VariableKind

    def get_name(self) -> str:
        """Return the variable name."""
        return self.name

    # def dump(self, out, ind: int):
    #     return super().dump(out.write(self.name), ind)


class UnaryExprAST(ExprAST):
    """AST class for the unary operator."""

    def __init__(self, op_code: str, operand: ExprAST):
        """Initialize the UnaryExprAST instance."""
        super().__init__()
        self.op_code = op_code
        self.operand = operand
        self.kind = ExprKind.UnaryOpKind

    # def dump(self, out, ind: int):
    #     super().dump(out.write("unary" + self.op_code), ind)
    #     self.operand.dump(out, ind + 1)


class BinaryExprAST(ExprAST):
    """AST class for the binary operator."""

    def __init__(
        self, loc: SourceLocation, op: str, lhs: ExprAST, rhs: ExprAST
    ):
        """Initialize the BinaryExprAST instance."""
        super().__init__(loc)
        self.op = op
        self.lhs = lhs
        self.rhs = rhs
        self.kind = ExprKind.BinaryOpKind

    # def dump(self, out, ind: int):
    #     super().dump(out.write("binary" + self.op), ind)
    #     self.lhs.dump(indent(out, ind).write("lhs:"), ind + 1)
    #     self.rhs.dump(indent(out, ind).write("rhs:"), ind + 1)


class CallExprAST(ExprAST):
    """AST class for function call."""

    def __init__(self, loc: SourceLocation, callee: str, args: List[ExprAST]):
        """Initialize the CallExprAST instance."""
        super().__init__(loc)
        self.callee = callee
        self.args = args
        self.kind = ExprKind.CallKind

    # def dump(self, out, ind: int):
    #     super().dump(out.write("call " + self.callee), ind)
    #     for arg in self.args:
    #         arg.dump(indent(out, ind + 1), ind + 1)


class IfExprAST(ExprAST):
    """AST class for `if` statement."""

    def __init__(
        self,
        loc: SourceLocation,
        cond: ExprAST,
        then_: ExprAST,
        else_: ExprAST,
    ):
        """Initialize the IfExprAST instance."""
        super().__init__(loc)
        self.cond = cond
        self.then_ = then_
        self.else_ = else_
        self.kind = ExprKind.IfKind

    # def dump(self, out, ind: int):
    #     super().dump(out.write("if"), ind)
    #     self.cond.dump(indent(out, ind).write("cond:"), ind + 1)
    #     self.then_.dump(indent(out, ind).write("then:"), ind + 1)
    #     self.else_.dump(indent(out, ind).write("else:"), ind + 1)


class ForExprAST(ExprAST):
    """AST class for `For` statement."""

    var_name: str
    start: ExprAST
    end: ExprAST
    step: ExprAST
    body: ExprAST

    def __init__(
        self,
        var_name: str,
        start: ExprAST,
        end: ExprAST,
        step: ExprAST,
        body: ExprAST,
    ):
        """Initialize the ForExprAST instance."""
        super().__init__()
        self.var_name = var_name
        self.start = start
        self.end = end
        self.step = step
        self.body = body
        self.kind = ExprKind.ForKind

    # def dump(self, out, ind: int):
    #     super().dump(out.write("for"), ind)
    #     self.start.dump(indent(out, ind).write("start:"), ind + 1)
    #     self.end.dump(indent(out, ind).write("end:"), ind + 1)
    #     self.step.dump(indent(out, ind).write("step:"), ind + 1)
    #     self.body.dump(indent(out, ind).write("body:"), ind + 1)


class VarExprAST(ExprAST):
    """AST class for variable declaration."""

    def __init__(
        self,
        var_names: List[Tuple[str, ExprAST]],
        type_name: str,
        body: ExprAST,
    ):
        """Initialize the VarExprAST instance."""
        super().__init__()
        self.var_names = var_names
        self.type_name = type_name
        self.body = body
        self.kind = ExprKind.VarKind

    # def dump(self, out, ind: int):
    #     super().dump(out.write("var"), ind)
    #     for name, expr in self.var_names:
    #         expr.dump(indent(out, ind).write(name + ":"), ind + 1)
    #     self.body.dump(indent(out, ind).write("body:"), ind + 1)


class PrototypeAST(ExprAST):
    """AST class for function prototype declaration."""

    def __init__(
        self,
        loc: SourceLocation,
        name: str,
        type_name: str,
        args: List[VariableExprAST],
    ):
        """Initialize the PrototypeAST instance."""
        super().__init__()
        self.name = name
        self.args = args
        self.type_name = type_name
        self.line = loc.line
        self.kind = ExprKind.PrototypeKind

    def get_name(self) -> str:
        """Return the prototype name."""
        return self.name

    def get_line(self) -> int:
        """Return the line number of the occurrence of the expression."""
        return self.line


class ReturnExprAST(ExprAST):
    """AST class for function `return` statement."""

    def __init__(self, expr: ExprAST):
        """Initialize the ReturnExprAST instance."""
        super().__init__()
        self.expr = expr
        self.kind = ExprKind.ReturnKind

    # def dump(self, out, ind: int):
    #     indent(out, ind).write("ReturnExprAST\n")
    #     ind += 1
    #     indent(out, ind).write("expr:")
    #     if self.expr:
    #         self.expr.dump(out, ind)
    #     else:
    #         out.write("null\n")


class FunctionAST(ExprAST):
    """AST class for function definition."""

    def __init__(self, proto: PrototypeAST, body: ExprAST):
        """Initialize the FunctionAST instance."""
        super().__init__()
        self.proto = proto
        self.body = body
        self.kind = ExprKind.FunctionKind

    # def dump(self, out, ind: int):
    #     indent(out, ind).write("FunctionAST\n")
    #     ind += 1
    #     indent(out, ind).write("body:")
    #     if self.body:
    #         self.body.dump(out, ind)
    #     else:
    #         out.write("null\n")


class TreeAST(ExprAST):
    """The AST tree."""

    def __init__(self):
        """Initialize the TreeAST instance."""
        super().__init__()
        self.nodes = []
