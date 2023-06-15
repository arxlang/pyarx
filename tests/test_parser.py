from arx.io import ArxIO
from arx.lexer import Lexer, Token
from arx.parser import Parser


def test_get_next_token():
    """Test gettok for main tokens."""
    ArxIO.string_to_buffer(
        """
        fn math(x):
          if x > 10:
            x + 1
          else:
            x * 20

        math(1)
    """
    )

    Lexer.get_next_token()
    assert Lexer.cur_tok == Token.tok_function
    Lexer.get_next_token()
    assert Lexer.cur_tok == Token.tok_identifier
    Lexer.get_next_token()
    assert Lexer.cur_tok == "("
    Lexer.get_next_token()
    assert Lexer.cur_tok == Token.tok_identifier
    Lexer.get_next_token()
    assert Lexer.cur_tok == ")"
    Lexer.get_next_token()
    assert Lexer.cur_tok == ":"
    Lexer.get_next_token()
    assert Lexer.cur_tok == Token.tok_if
    Lexer.get_next_token()
    assert Lexer.cur_tok == Token.tok_identifier
    Lexer.get_next_token()
    assert Lexer.cur_tok == ">"
    Lexer.get_next_token()
    assert Lexer.cur_tok == Token.tok_float_literal
    Lexer.get_next_token()
    assert Lexer.cur_tok == ":"
    Lexer.get_next_token()
    assert Lexer.cur_tok == Token.tok_identifier
    Lexer.get_next_token()
    assert Lexer.cur_tok == "+"
    Lexer.get_next_token()
    assert Lexer.cur_tok == Token.tok_float_literal
    Lexer.get_next_token()
    assert Lexer.cur_tok == Token.tok_else
    Lexer.get_next_token()
    assert Lexer.cur_tok == ":"
    Lexer.get_next_token()
    assert Lexer.cur_tok == Token.tok_identifier
    Lexer.get_next_token()
    assert Lexer.cur_tok == "*"
    Lexer.get_next_token()
    assert Lexer.cur_tok == Token.tok_float_literal
    Lexer.get_next_token()
    assert Lexer.cur_tok == Token.tok_identifier
    Lexer.get_next_token()
    assert Lexer.cur_tok == "("
    Lexer.get_next_token()
    assert Lexer.cur_tok == Token.tok_float_literal
    Lexer.get_next_token()
    assert Lexer.cur_tok == ")"
    Lexer.get_next_token()
    assert Lexer.cur_tok == -1


def test_binop_precedence():
    Parser.setup()

    assert Parser.bin_op_precedence["="] == 2
    assert Parser.bin_op_precedence["<"] == 10
    assert Parser.bin_op_precedence["+"] == 20
    assert Parser.bin_op_precedence["-"] == 20
    assert Parser.bin_op_precedence["*"] == 40


def test_parse_float_expr():
    """Test gettok for main tokens"""

    ArxIO.string_to_buffer("1 2")

    tok = Lexer.get_next_token()
    assert tok == Token.tok_float_literal
    expr = Parser.parse_float_expr()
    assert expr
    assert expr.val == 1

    expr = Parser.parse_float_expr()
    assert expr
    assert expr.val == 2

    ArxIO.string_to_buffer("3")

    tok = Lexer.get_next_token()
    assert tok == Token.tok_float_literal
    expr = Parser.parse_float_expr()
    assert expr
    assert expr.val == 3


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
