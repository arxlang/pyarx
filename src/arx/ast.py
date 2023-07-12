"""AST classes and functions."""
from enum import Enum
from typing import List, Tuple

from arx.lexer import SourceLocation


class ExprKind(Enum):
    """The expression kind class used for downcasting."""

    GenericKind = -1
    ModuleKind = -2

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


class ExprAST:
    """AST main expression class."""

    loc: SourceLocation
    kind: ExprKind

    def __init__(self, loc: SourceLocation = SourceLocation(0, 0)) -> None:
        """Initialize the ExprAST instance."""
        self.kind = ExprKind.GenericKind
        self.loc = loc


class BlockAST(ExprAST):
    """The AST tree."""

    nodes: List[ExprAST]

    def __init__(self) -> None:
        """Initialize the BlockAST instance."""
        super().__init__()
        self.nodes: List[ExprAST] = []


class ModuleAST(BlockAST):
    """AST main expression class."""

    name: str

    def __init__(self, name: str) -> None:
        """Initialize the ExprAST instance."""
        super().__init__()
        self.name = name
        self.kind = ExprKind.ModuleKind


class FloatExprAST(ExprAST):
    """AST for the literal float number."""

    value: float

    def __init__(self, val: float) -> None:
        """Initialize the FloatAST instance."""
        super().__init__()
        self.value = val
        self.kind = ExprKind.FloatDTKind


class VariableExprAST(ExprAST):
    """AST class for the variable usage."""

    def __init__(self, loc: SourceLocation, name: str, type_name: str) -> None:
        """Initialize the VariableExprAST instance."""
        super().__init__(loc)
        self.name = name
        self.type_name = type_name
        self.kind = ExprKind.VariableKind

    def get_name(self) -> str:
        """Return the variable name."""
        return self.name


class UnaryExprAST(ExprAST):
    """AST class for the unary operator."""

    def __init__(self, op_code: str, operand: ExprAST) -> None:
        """Initialize the UnaryExprAST instance."""
        super().__init__()
        self.op_code = op_code
        self.operand = operand
        self.kind = ExprKind.UnaryOpKind


class BinaryExprAST(ExprAST):
    """AST class for the binary operator."""

    def __init__(
        self, loc: SourceLocation, op: str, lhs: ExprAST, rhs: ExprAST
    ) -> None:
        """Initialize the BinaryExprAST instance."""
        super().__init__(loc)
        self.op = op
        self.lhs = lhs
        self.rhs = rhs
        self.kind = ExprKind.BinaryOpKind


class CallExprAST(ExprAST):
    """AST class for function call."""

    def __init__(
        self, loc: SourceLocation, callee: str, args: List[ExprAST]
    ) -> None:
        """Initialize the CallExprAST instance."""
        super().__init__(loc)
        self.callee = callee
        self.args = args
        self.kind = ExprKind.CallKind


class IfStmtAST(ExprAST):
    """AST class for `if` statement."""

    cond: ExprAST
    then_: BlockAST
    else_: BlockAST

    def __init__(
        self,
        loc: SourceLocation,
        cond: ExprAST,
        then_: BlockAST,
        else_: BlockAST,
    ) -> None:
        """Initialize the IfStmtAST instance."""
        super().__init__(loc)
        self.cond = cond
        self.then_ = then_
        self.else_ = else_
        self.kind = ExprKind.IfKind


class ForStmtAST(ExprAST):
    """AST class for `For` statement."""

    var_name: str
    start: ExprAST
    end: ExprAST
    step: ExprAST
    body: BlockAST

    def __init__(
        self,
        var_name: str,
        start: ExprAST,
        end: ExprAST,
        step: ExprAST,
        body: BlockAST,
    ) -> None:
        """Initialize the ForStmtAST instance."""
        super().__init__()
        self.var_name = var_name
        self.start = start
        self.end = end
        self.step = step
        self.body = body
        self.kind = ExprKind.ForKind


class VarExprAST(ExprAST):
    """AST class for variable declaration."""

    var_names: List[Tuple[str, ExprAST]]
    type_name: str
    body: ExprAST

    def __init__(
        self,
        var_names: List[Tuple[str, ExprAST]],
        type_name: str,
        body: ExprAST,
    ) -> None:
        """Initialize the VarExprAST instance."""
        super().__init__()
        self.var_names = var_names
        self.type_name = type_name
        self.body = body
        self.kind = ExprKind.VarKind


class PrototypeAST(ExprAST):
    """AST class for function prototype declaration."""

    name: str
    args: List[VariableExprAST]
    type_name: str

    def __init__(
        self,
        loc: SourceLocation,
        name: str,
        type_name: str,
        args: List[VariableExprAST],
    ) -> None:
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


class ReturnStmtAST(ExprAST):
    """AST class for function `return` statement."""

    value: ExprAST

    def __init__(self, value: ExprAST) -> None:
        """Initialize the ReturnStmtAST instance."""
        super().__init__()
        self.value = value
        self.kind = ExprKind.ReturnKind


class FunctionAST(ExprAST):
    """AST class for function definition."""

    proto: PrototypeAST
    body: BlockAST

    def __init__(self, proto: PrototypeAST, body: BlockAST) -> None:
        """Initialize the FunctionAST instance."""
        super().__init__()
        self.proto = proto
        self.body = body
        self.kind = ExprKind.FunctionKind
