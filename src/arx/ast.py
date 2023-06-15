from abc import ABC, abstractmethod
from enum import Enum
from typing import List, Tuple

from arx.lexer import Lexer, SourceLocation


class ExprKind(Enum):
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


class Visitor(ABC):
    @abstractmethod
    def visit(self, node: "ExprAST"):
        pass

    @abstractmethod
    def clean(self):
        pass


class ExprAST:
    def __init__(self, loc: SourceLocation = Lexer.cur_loc):
        self.kind = ExprKind.GenericKind
        self.loc = loc

    def get_line(self) -> int:
        return self.loc.line

    def get_col(self) -> int:
        return self.loc.col

    def accept(self, visitor: Visitor):
        """
        Accepts a visitor and invokes the appropriate visit method based on the expression kind.

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

    def dump(self, out, ind: int):
        return out.write(f":{self.get_line()}:{self.get_col()}\n")


class FloatExprAST(ExprAST):
    def __init__(self, val: float):
        super().__init__()
        self.val = val
        self.kind = ExprKind.FloatDTKind

    def dump(self, out, ind: int):
        return super().dump(out.write(str(self.val)), ind)


class VariableExprAST(ExprAST):
    def __init__(self, loc: SourceLocation, name: str, type_name: str):
        super().__init__(loc)
        self.name = name
        self.type_name = type_name
        self.kind = ExprKind.VariableKind

    def get_name(self) -> str:
        return self.name

    def dump(self, out, ind: int):
        return super().dump(out.write(self.name), ind)


class UnaryExprAST(ExprAST):
    def __init__(self, op_code: str, operand: ExprAST):
        super().__init__()
        self.op_code = op_code
        self.operand = operand
        self.kind = ExprKind.UnaryOpKind

    def dump(self, out, ind: int):
        super().dump(out.write("unary" + self.op_code), ind)
        self.operand.dump(out, ind + 1)


class BinaryExprAST(ExprAST):
    def __init__(
        self, loc: SourceLocation, op: str, lhs: ExprAST, rhs: ExprAST
    ):
        super().__init__(loc)
        self.op = op
        self.lhs = lhs
        self.rhs = rhs
        self.kind = ExprKind.BinaryOpKind

    def dump(self, out, ind: int):
        super().dump(out.write("binary" + self.op), ind)
        self.lhs.dump(indent(out, ind).write("lhs:"), ind + 1)
        self.rhs.dump(indent(out, ind).write("rhs:"), ind + 1)


class CallExprAST(ExprAST):
    def __init__(self, loc: SourceLocation, callee: str, args: List[ExprAST]):
        super().__init__(loc)
        self.callee = callee
        self.args = args
        self.kind = ExprKind.CallKind

    def dump(self, out, ind: int):
        super().dump(out.write("call " + self.callee), ind)
        for arg in self.args:
            arg.dump(indent(out, ind + 1), ind + 1)


class IfExprAST(ExprAST):
    def __init__(
        self,
        loc: SourceLocation,
        cond: ExprAST,
        then_: ExprAST,
        else_: ExprAST,
    ):
        super().__init__(loc)
        self.cond = cond
        self.then_ = then_
        self.else_ = else_
        self.kind = ExprKind.IfKind

    def dump(self, out, ind: int):
        super().dump(out.write("if"), ind)
        self.cond.dump(indent(out, ind).write("cond:"), ind + 1)
        self.then_.dump(indent(out, ind).write("then:"), ind + 1)
        self.else_.dump(indent(out, ind).write("else:"), ind + 1)


class ForExprAST(ExprAST):
    def __init__(
        self,
        var_name: str,
        start: ExprAST,
        end: ExprAST,
        step: ExprAST,
        body: ExprAST,
    ):
        super().__init__()
        self.var_name = var_name
        self.start = start
        self.end = end
        self.step = step
        self.body = body
        self.kind = ExprKind.ForKind

    def dump(self, out, ind: int):
        super().dump(out.write("for"), ind)
        self.start.dump(indent(out, ind).write("start:"), ind + 1)
        self.end.dump(indent(out, ind).write("end:"), ind + 1)
        self.step.dump(indent(out, ind).write("step:"), ind + 1)
        self.body.dump(indent(out, ind).write("body:"), ind + 1)


class VarExprAST(ExprAST):
    def __init__(
        self,
        var_names: List[Tuple[str, ExprAST]],
        type_name: str,
        body: ExprAST,
    ):
        super().__init__()
        self.var_names = var_names
        self.type_name = type_name
        self.body = body
        self.kind = ExprKind.VarKind

    def dump(self, out, ind: int):
        super().dump(out.write("var"), ind)
        for name, expr in self.var_names:
            expr.dump(indent(out, ind).write(name + ":"), ind + 1)
        self.body.dump(indent(out, ind).write("body:"), ind + 1)


class PrototypeAST(ExprAST):
    def __init__(
        self,
        loc: SourceLocation,
        name: str,
        type_name: str,
        args: List[VariableExprAST],
    ):
        super().__init__()
        self.name = name
        self.args = args
        self.type_name = type_name
        self.line = loc.line
        self.kind = ExprKind.PrototypeKind

    def get_name(self) -> str:
        return self.name

    def get_line(self) -> int:
        return self.line


class ReturnExprAST(ExprAST):
    def __init__(self, expr: ExprAST):
        super().__init__()
        self.expr = expr
        self.kind = ExprKind.ReturnKind

    def dump(self, out, ind: int):
        indent(out, ind).write("ReturnExprAST\n")
        ind += 1
        indent(out, ind).write("expr:")
        if self.expr:
            self.expr.dump(out, ind)
        else:
            out.write("null\n")


class FunctionAST(ExprAST):
    def __init__(self, proto: PrototypeAST, body: ExprAST):
        super().__init__()
        self.proto = proto
        self.body = body
        self.kind = ExprKind.FunctionKind

    def dump(self, out, ind: int):
        indent(out, ind).write("FunctionAST\n")
        ind += 1
        indent(out, ind).write("body:")
        if self.body:
            self.body.dump(out, ind)
        else:
            out.write("null\n")


class TreeAST(ExprAST):
    def __init__(self):
        super().__init__()
        self.nodes = []
