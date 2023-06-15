"""Tests for `arx`.`lexer`."""
import pytest

from arx.io import ArxIO
from arx.lexer import Lexer, Token


def test_token_name():
    assert Lexer.get_tok_name(Token.tok_eof) == "eof"
    assert Lexer.get_tok_name(Token.tok_function) == "function"
    assert Lexer.get_tok_name(Token.tok_return) == "return"
    assert Lexer.get_tok_name(Token.tok_identifier) == "identifier"
    assert Lexer.get_tok_name(Token.tok_if) == "if"
    assert Lexer.get_tok_name(Token.tok_for) == "for"
    assert Lexer.get_tok_name("+") == "+"


@pytest.mark.parametrize("value", ["123", "234", "345"])
def test_advance(value):
    ArxIO.string_to_buffer(value)
    assert Lexer.advance() == value[0]
    assert Lexer.advance() == value[1]
    assert Lexer.advance() == value[2]


def test_get_tok_simple():
    ArxIO.string_to_buffer("11")
    assert Lexer.gettok() == Token.tok_float_literal
    assert Lexer.num_float == 11

    ArxIO.string_to_buffer("21")
    assert Lexer.gettok() == Token.tok_float_literal
    assert Lexer.num_float == 21

    ArxIO.string_to_buffer("31")
    assert Lexer.gettok() == Token.tok_float_literal
    assert Lexer.num_float == 31


def test_get_next_token_simple():
    ArxIO.string_to_buffer("11")
    assert Lexer.get_next_token() == Token.tok_float_literal
    assert Lexer.num_float == 11

    ArxIO.string_to_buffer("21")
    assert Lexer.get_next_token() == Token.tok_float_literal
    assert Lexer.num_float == 21

    ArxIO.string_to_buffer("31")
    assert Lexer.get_next_token() == Token.tok_float_literal
    assert Lexer.num_float == 31


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

    assert Lexer.gettok() == Token.tok_function
    assert Lexer.gettok() == Token.tok_identifier
    assert Lexer.gettok() == "("
    assert Lexer.gettok() == Token.tok_identifier
    assert Lexer.gettok() == ")"
    assert Lexer.gettok() == ":"
    assert Lexer.gettok() == Token.tok_if
    assert Lexer.gettok() == Token.tok_identifier
    assert Lexer.gettok() == ">"
    assert Lexer.gettok() == Token.tok_float_literal
    assert Lexer.gettok() == ":"
    assert Lexer.gettok() == Token.tok_identifier
    assert Lexer.gettok() == "+"
    assert Lexer.gettok() == Token.tok_float_literal
    assert Lexer.gettok() == Token.tok_else
    assert Lexer.gettok() == ":"
    assert Lexer.gettok() == Token.tok_identifier
    assert Lexer.gettok() == "*"
    assert Lexer.gettok() == Token.tok_float_literal
    assert Lexer.gettok() == Token.tok_identifier
    assert Lexer.gettok() == "("
    assert Lexer.gettok() == Token.tok_float_literal
    assert Lexer.gettok() == ")"
