import astx
from arx.io import ArxIO
from arx.lexer import Lexer
from arx.parser import Parser


def test_binop_precedence() -> None:
    """Test BinOp precedence."""
    lexer = Lexer()
    parser = Parser(lexer.lex())

    assert parser.bin_op_precedence["="] == 2
    assert parser.bin_op_precedence["<"] == 10
    assert parser.bin_op_precedence[">"] == 10
    assert parser.bin_op_precedence["+"] == 20
    assert parser.bin_op_precedence["-"] == 20
    assert parser.bin_op_precedence["*"] == 40


def test_parse_int32_expr() -> None:
    """Test gettok for main tokens"""
    ArxIO.string_to_buffer("1 2")
    lexer = Lexer()
    parser = Parser(lexer.lex())

    parser.tokens.get_next_token()
    expr = parser.parse_int32_expr()
    assert expr
    assert isinstance(expr, astx.LiteralInt32)
    assert expr.value == 1

    expr = parser.parse_int32_expr()
    assert expr
    assert isinstance(expr, astx.LiteralInt32)
    assert expr.value == 2

    ArxIO.string_to_buffer("3")
    parser = Parser(lexer.lex())

    tok = parser.tokens.get_next_token()
    expr = parser.parse_int32_expr()
    assert expr
    assert isinstance(expr, astx.LiteralInt32)
    assert expr.value == 3


def test_parse() -> None:
    """Test gettok for main tokens."""
    ArxIO.string_to_buffer(
        "if 1 > 2:\n" + "  a = 1\n" + "else:\n" + "  a = 2\n"
    )
    lexer = Lexer()
    parser = Parser()

    expr = parser.parse(lexer.lex())
    assert expr
    assert isinstance(expr, astx.Block)


def test_parse_if_stmt() -> None:
    """Test gettok for main tokens."""
    ArxIO.string_to_buffer(
        "if 1 > 2:\n" + "  a = 1\n" + "else:\n" + "  a = 2\n"
    )

    lexer = Lexer()
    parser = Parser(lexer.lex())

    parser.tokens.get_next_token()
    expr = parser.parse_primary()
    assert expr
    assert isinstance(expr, astx.If)
    assert isinstance(expr.condition, astx.BinaryOp)
    assert isinstance(expr.then, astx.Block)
    assert isinstance(expr.then.nodes[0], astx.BinaryOp)
    assert isinstance(expr.else_, astx.Block)
    assert isinstance(expr.else_.nodes[0], astx.BinaryOp)


def test_parse_fn() -> None:
    """Test gettok for main tokens."""
    ArxIO.string_to_buffer(
        "fn math(x):\n"
        + "  if 1 > 2:\n"
        + "    a = 1\n"
        + "  else:\n"
        + "    a = 2\n"
        + "  return a\n"
    )

    lexer = Lexer()
    parser = Parser(lexer.lex())

    parser.tokens.get_next_token()
    expr = parser.parse_function()
    assert expr
    assert isinstance(expr, astx.Function)
    assert isinstance(expr.prototype, astx.FunctionPrototype)
    assert isinstance(expr.prototype.args[0], astx.Variable)
    assert isinstance(expr.body, astx.Block)
    assert isinstance(expr.body.nodes[0], astx.If)
    assert isinstance(expr.body.nodes[0].condition, astx.BinaryOp)
    assert isinstance(expr.body.nodes[0].then, astx.Block)
    assert isinstance(expr.body.nodes[0].then.nodes[0], astx.BinaryOp)
    assert isinstance(expr.body.nodes[0].else_, astx.Block)
    assert isinstance(expr.body.nodes[0].else_.nodes[0], astx.BinaryOp)
    assert isinstance(expr.body.nodes[1], astx.FunctionReturn)
    assert isinstance(expr.body.nodes[1].value, astx.Variable)
    assert expr.body.nodes[1].value.name == "a"
