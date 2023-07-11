from arx.io import ArxIO
from arx import ast
from arx.lexer import Lexer, TokenKind, Token
from arx.parser import Parser


def test_binop_precedence() -> None:
    """Test BinOp precedence."""
    Parser.clean()

    assert Parser.bin_op_precedence["="] == 2
    assert Parser.bin_op_precedence["<"] == 10
    assert Parser.bin_op_precedence[">"] == 10
    assert Parser.bin_op_precedence["+"] == 20
    assert Parser.bin_op_precedence["-"] == 20
    assert Parser.bin_op_precedence["*"] == 40


def test_parse_float_expr() -> None:
    """Test gettok for main tokens"""
    ArxIO.string_to_buffer("1 2")
    Parser.clean()

    Lexer.get_next_token()
    expr = Parser.parse_float_expr()
    assert expr
    assert isinstance(expr, ast.FloatExprAST)
    assert expr.value == 1.0

    expr = Parser.parse_float_expr()
    assert expr
    assert isinstance(expr, ast.FloatExprAST)
    assert expr.value == 2

    ArxIO.string_to_buffer("3")

    tok = Lexer.get_next_token()
    expr = Parser.parse_float_expr()
    assert expr
    assert isinstance(expr, ast.FloatExprAST)
    assert expr.value == 3


def test_parse() -> None:
    """Test gettok for main tokens."""
    Parser.clean()
    ArxIO.string_to_buffer(
        "if 1 > 2:\n" + "  a = 1\n" + "else:\n" + "  a = 2\n"
    )

    expr = Parser.parse()
    assert expr
    assert isinstance(expr, ast.BlockAST)


def test_parse_if_stmt() -> None:
    """Test gettok for main tokens."""
    Parser.clean()
    ArxIO.string_to_buffer(
        "if 1 > 2:\n" + "  a = 1\n" + "else:\n" + "  a = 2\n"
    )

    Lexer.get_next_token()
    expr = Parser.parse_primary()
    assert expr
    assert isinstance(expr, ast.IfStmtAST)
    assert isinstance(expr.cond, ast.BinaryExprAST)
    assert isinstance(expr.then_, ast.BlockAST)
    assert isinstance(expr.then_.nodes[0], ast.BinaryExprAST)
    assert isinstance(expr.else_, ast.BlockAST)
    assert isinstance(expr.else_.nodes[0], ast.BinaryExprAST)


def test_parse_fn() -> None:
    """Test gettok for main tokens."""
    Parser.clean()
    ArxIO.string_to_buffer(
        "fn math(x):\n"
        + "  if 1 > 2:\n"
        + "    a = 1\n"
        + "  else:\n"
        + "    a = 2\n"
        + "  return a\n"
    )
    Lexer.get_next_token()
    expr = Parser.parse_function()
    assert expr
    assert isinstance(expr, ast.FunctionAST)
    assert isinstance(expr.proto, ast.PrototypeAST)
    assert isinstance(expr.proto.args[0], ast.VariableExprAST)
    assert isinstance(expr.body, ast.BlockAST)
    assert isinstance(expr.body.nodes[0], ast.IfStmtAST)
    assert isinstance(expr.body.nodes[0].cond, ast.BinaryExprAST)
    assert isinstance(expr.body.nodes[0].then_, ast.BlockAST)
    assert isinstance(expr.body.nodes[0].then_.nodes[0], ast.BinaryExprAST)
    assert isinstance(expr.body.nodes[0].else_, ast.BlockAST)
    assert isinstance(expr.body.nodes[0].else_.nodes[0], ast.BinaryExprAST)
    assert isinstance(expr.body.nodes[1], ast.ReturnStmtAST)
    assert isinstance(expr.body.nodes[1].value, ast.VariableExprAST)
    assert expr.body.nodes[1].value.name == "a"
