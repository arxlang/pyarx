"""Tests for `arx`.`lexer`."""
import pytest

from arx.io import ArxIO
from arx.lexer import Lexer, TokenKind, Token


def test_token_name() -> None:
    assert Token(kind=TokenKind.eof, value="").get_name() == "eof"
    assert Token(kind=TokenKind.kw_function, value="").get_name() == "function"
    assert Token(kind=TokenKind.kw_return, value="").get_name() == "return"
    assert (
        Token(kind=TokenKind.identifier, value="").get_name() == "identifier"
    )
    assert Token(kind=TokenKind.kw_if, value="").get_name() == "if"
    assert Token(kind=TokenKind.kw_for, value="").get_name() == "for"
    assert Token(kind=TokenKind.operator, value="+").get_name() == "+"
    assert Token(kind=TokenKind.operator, value="+").get_name() == "+"


@pytest.mark.parametrize("value", ["123", "234", "345"])
def test_advance(value: str) -> None:
    ArxIO.string_to_buffer(value)
    lex = Lexer()
    assert lex.advance() == value[0]
    assert lex.advance() == value[1]
    assert lex.advance() == value[2]


def test_get_tok_simple() -> None:
    ArxIO.string_to_buffer("11")
    lex = Lexer()
    assert lex.get_token() == Token(kind=TokenKind.float_literal, value=11.0)

    ArxIO.string_to_buffer("21")
    assert lex.get_token() == Token(kind=TokenKind.float_literal, value=21.0)

    ArxIO.string_to_buffer("31")
    assert lex.get_token() == Token(kind=TokenKind.float_literal, value=31.0)


def test_get_next_token_simple() -> None:
    lex = Lexer()
    ArxIO.string_to_buffer("11")
    tokens = lex.run()
    assert tokens.get_next_token() == Token(
        kind=TokenKind.float_literal, value=11.0
    )

    ArxIO.string_to_buffer("21")
    tokens = lex.run()
    assert tokens.get_next_token() == Token(
        kind=TokenKind.float_literal, value=21.0
    )

    ArxIO.string_to_buffer("31")
    tokens = lex.run()
    assert tokens.get_next_token() == Token(
        kind=TokenKind.float_literal, value=31.0
    )


def test_get_tok() -> None:
    """Test gettok for main tokens."""
    ArxIO.string_to_buffer(
        "fn math(x):\n"
        "  if x > 10:\n"
        "    return x + 1\n"
        "  else:\n"
        "    return x * 20\n"
        "math(1)\n"
    )
    lex = Lexer()
    assert lex.get_token() == Token(kind=TokenKind.kw_function, value="fn")
    assert lex.get_token() == Token(kind=TokenKind.identifier, value="math")
    assert lex.get_token() == Token(kind=TokenKind.operator, value="(")
    assert lex.get_token() == Token(kind=TokenKind.identifier, value="x")
    assert lex.get_token() == Token(kind=TokenKind.operator, value=")")
    assert lex.get_token() == Token(kind=TokenKind.operator, value=":")
    assert lex.get_token() == Token(kind=TokenKind.indent, value=2)
    assert lex.get_token() == Token(kind=TokenKind.kw_if, value="if")
    assert lex.get_token() == Token(kind=TokenKind.identifier, value="x")
    assert lex.get_token() == Token(kind=TokenKind.operator, value=">")
    assert lex.get_token() == Token(kind=TokenKind.float_literal, value=10.0)
    assert lex.get_token() == Token(kind=TokenKind.operator, value=":")
    assert lex.get_token() == Token(kind=TokenKind.indent, value=4)
    assert lex.get_token() == Token(kind=TokenKind.kw_return, value="return")
    assert lex.get_token() == Token(kind=TokenKind.identifier, value="x")
    assert lex.get_token() == Token(kind=TokenKind.operator, value="+")
    assert lex.get_token() == Token(kind=TokenKind.float_literal, value=1.0)
    assert lex.get_token() == Token(kind=TokenKind.indent, value=2)
    assert lex.get_token() == Token(kind=TokenKind.kw_else, value="else")
    assert lex.get_token() == Token(kind=TokenKind.operator, value=":")
    assert lex.get_token() == Token(kind=TokenKind.indent, value=4)
    assert lex.get_token() == Token(kind=TokenKind.kw_return, value="return")
    assert lex.get_token() == Token(kind=TokenKind.identifier, value="x")
    assert lex.get_token() == Token(kind=TokenKind.operator, value="*")
    assert lex.get_token() == Token(kind=TokenKind.float_literal, value=20.0)
    assert lex.get_token() == Token(kind=TokenKind.identifier, value="math")
    assert lex.get_token() == Token(kind=TokenKind.operator, value="(")
    assert lex.get_token() == Token(kind=TokenKind.float_literal, value=1.0)
    assert lex.get_token() == Token(kind=TokenKind.operator, value=")")
