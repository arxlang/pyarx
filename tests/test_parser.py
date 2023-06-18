from arx.io import ArxIO
from arx import ast
from arx.lexer import Lexer, TokenKind, Token
from arx.parser import Parser


def test_binop_precedence():
    assert Parser.bin_op_precedence["="] == 2
    assert Parser.bin_op_precedence["<"] == 10
    assert Parser.bin_op_precedence[">"] == 10
    assert Parser.bin_op_precedence["+"] == 20
    assert Parser.bin_op_precedence["-"] == 20
    assert Parser.bin_op_precedence["*"] == 40


def test_parse_float_expr():
    """Test gettok for main tokens"""

    ArxIO.string_to_buffer("1 2")

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


def test_parse():
    """Test gettok for main tokens."""
    ArxIO.string_to_buffer(
        """
        if 1 > 2:
          a = 1
        else:
          a = 2
        """
    )

    expr = Parser.parse()
    assert expr
    assert isinstance(expr, ast.TreeAST)


def test_parse_if_expr():
    """Test gettok for main tokens."""
    ArxIO.string_to_buffer(
        """
        if 1 > 2:
          a = 1
        else:
          a = 2
        """
    )

    Lexer.get_next_token()
    expr = Parser.parse_primary()
    assert expr
    assert isinstance(expr, ast.IfExprAST)
    assert isinstance(expr.cond, ast.BinaryExprAST)
    assert isinstance(expr.then_, ast.BinaryExprAST)
    assert isinstance(expr.else_, ast.BinaryExprAST)


def test_parse_fn():
    """Test gettok for main tokens."""
    ArxIO.string_to_buffer(
        """
        fn math(x):
          if 1 > 2:
            a = 1
          else:
            a = 2
        """
    )

    Lexer.get_next_token()
    expr = Parser.parse_definition()
    assert expr
    assert isinstance(expr, ast.FunctionAST)
    assert isinstance(expr.proto, ast.PrototypeAST)
    assert isinstance(expr.proto.args[0], ast.VariableExprAST)
    assert isinstance(expr.body, ast.IfExprAST)
    assert isinstance(expr.body.cond, ast.BinaryExprAST)
    assert isinstance(expr.body.then_, ast.BinaryExprAST)
    assert isinstance(expr.body.else_, ast.BinaryExprAST)
