"""Tests for `arx`.`lexer`."""
import pytest

from arx.io import ArxIO
from arx.lexer import Lexer, TokenKind, Token


def test_token_name():
    assert Token(kind=TokenKind.eof, value="").get_name() == "eof"
    assert Token(kind=TokenKind.kw_function, value="").get_name() == "function"
    assert Token(kind=TokenKind.kw_return, value="").get_name() == "return"
    assert (
        Token(kind=TokenKind.identifier, value="").get_name() == "identifier"
    )
    assert Token(kind=TokenKind.kw_if, value="").get_name() == "if"
    assert Token(kind=TokenKind.kw_for, value="").get_name() == "for"
    assert Token(kind=TokenKind.operator, value="+").get_name() == "+"


@pytest.mark.parametrize("value", ["123", "234", "345"])
def test_advance(value):
    ArxIO.string_to_buffer(value)
    assert Lexer.advance() == value[0]
    assert Lexer.advance() == value[1]
    assert Lexer.advance() == value[2]


def test_get_tok_simple():
    ArxIO.string_to_buffer("11")
    assert Lexer.gettok() == Token(kind=TokenKind.float_literal, value=11.0)

    ArxIO.string_to_buffer("21")
    assert Lexer.gettok() == Token(kind=TokenKind.float_literal, value=21.0)

    ArxIO.string_to_buffer("31")
    assert Lexer.gettok() == Token(kind=TokenKind.float_literal, value=31.0)


def test_get_next_token_simple():
    ArxIO.string_to_buffer("11")
    assert Lexer.get_next_token() == Token(
        kind=TokenKind.float_literal, value=11.0
    )

    ArxIO.string_to_buffer("21")
    assert Lexer.get_next_token() == Token(
        kind=TokenKind.float_literal, value=21.0
    )

    ArxIO.string_to_buffer("31")
    assert Lexer.get_next_token() == Token(
        kind=TokenKind.float_literal, value=31.0
    )


def test_get_tok():
    """Test gettok for main tokens"""
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

    assert Lexer.gettok() == Token(kind=TokenKind.kw_function, value="fn")
    assert Lexer.gettok() == Token(kind=TokenKind.identifier, value="math")
    assert Lexer.gettok() == Token(kind=TokenKind.operator, value="(")
    assert Lexer.gettok() == Token(kind=TokenKind.identifier, value="x")
    assert Lexer.gettok() == Token(kind=TokenKind.operator, value=")")
    assert Lexer.gettok() == Token(kind=TokenKind.operator, value=":")
    assert Lexer.gettok() == Token(kind=TokenKind.kw_if, value="if")
    assert Lexer.gettok() == Token(kind=TokenKind.identifier, value="x")
    assert Lexer.gettok() == Token(kind=TokenKind.operator, value=">")
    assert Lexer.gettok() == Token(kind=TokenKind.float_literal, value=10.0)
    assert Lexer.gettok() == Token(kind=TokenKind.operator, value=":")
    assert Lexer.gettok() == Token(kind=TokenKind.identifier, value="x")
    assert Lexer.gettok() == Token(kind=TokenKind.operator, value="+")
    assert Lexer.gettok() == Token(kind=TokenKind.float_literal, value=1.0)
    assert Lexer.gettok() == Token(kind=TokenKind.kw_else, value="else")
    assert Lexer.gettok() == Token(kind=TokenKind.operator, value=":")
    assert Lexer.gettok() == Token(kind=TokenKind.identifier, value="x")
    assert Lexer.gettok() == Token(kind=TokenKind.operator, value="*")
    assert Lexer.gettok() == Token(kind=TokenKind.float_literal, value=20.0)
    assert Lexer.gettok() == Token(kind=TokenKind.identifier, value="math")
    assert Lexer.gettok() == Token(kind=TokenKind.operator, value="(")
    assert Lexer.gettok() == Token(kind=TokenKind.float_literal, value=1.0)
    assert Lexer.gettok() == Token(kind=TokenKind.operator, value=")")
