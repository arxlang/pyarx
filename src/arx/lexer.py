"""Module for handling the lexer analysis."""
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict

from arx.io import ArxIO

EOF = ""


class SourceLocation:
    """
    Represents the source location with line and column information.

    Attributes
    ----------
    line : int
        Line number.
    col : int
        Column number.
    """

    def __init__(self, line: int, col: int) -> None:
        self.line = line
        self.col = col


class TokenKind(Enum):
    """TokenKind enumeration for known variables returned by the lexer."""

    eof: int = -1

    # function
    kw_function: int = -2
    kw_extern: int = -3
    kw_return: int = -4

    # data types
    identifier: int = -10
    float_literal: int = -11

    # control flow
    kw_if: int = -20
    kw_then: int = -21
    kw_else: int = -22
    kw_for: int = -23
    kw_in: int = -24

    # operators
    binary_op: int = -30
    unary_op: int = -31
    operator: int = -32

    # variables
    kw_var: int = -40
    kw_const: int = -41

    # flow and structure control
    indent = -50
    dedent = -51

    # generic control
    not_initialized: int = -9999


MAP_NAME_TO_KW_TOKEN = {
    "fn": TokenKind.kw_function,
    "return": TokenKind.kw_return,
    "extern": TokenKind.kw_extern,
    "if": TokenKind.kw_if,
    "else": TokenKind.kw_else,
    "for": TokenKind.kw_for,
    "in": TokenKind.kw_in,
    "binary": TokenKind.binary_op,
    "unary": TokenKind.unary_op,
    "var": TokenKind.kw_var,
    "operator": TokenKind.operator,
}


MAP_KW_TOKEN_TO_NAME: Dict[TokenKind, str] = {
    TokenKind.eof: "eof",
    TokenKind.kw_function: "function",
    TokenKind.kw_return: "return",
    TokenKind.kw_extern: "extern",
    TokenKind.identifier: "identifier",
    TokenKind.indent: "indent",
    TokenKind.float_literal: "float",
    TokenKind.kw_if: "if",
    TokenKind.kw_then: "then",
    TokenKind.kw_else: "else",
    TokenKind.kw_for: "for",
    TokenKind.kw_in: "in",
    # TokenKind.kw_binary_op: "binary",
    # TokenKind.kw_unary_op: "unary",
    TokenKind.kw_var: "var",
    TokenKind.kw_const: "const",
}


@dataclass
class Token:
    """Token class store the kind and the value of the token."""

    kind: TokenKind
    value: Any

    def get_name(self) -> str:
        """
        Get the name of the specified token.

        Parameters
        ----------
        tok : int
            TokenKind value.

        Returns
        -------
        str
            Name of the token.
        """
        return MAP_KW_TOKEN_TO_NAME.get(self.kind, str(self.value))

    def get_display_value(self) -> str:
        """
        Return the string representation of a token value.

        Returns
        -------
            str: The string representation of the token value.
        """
        if self.kind == TokenKind.identifier:
            return "(" + self.value + ")"
        if self.kind == TokenKind.indent:
            return "(" + str(self.value) + ")"
        elif self.kind == TokenKind.float_literal:
            return "(" + str(self.value) + ")"
        else:
            return ""

    def __str__(self):
        """Display the token in a readable way."""
        return f"{self.get_name()}{self.get_display_value()}"


class Lexer:
    """
    Lexer class for tokenizing known variables.

    Attributes
    ----------
    cur_loc : SourceLocation
        Current source location.
    cur_tok : int
        Current token.
    lex_loc : SourceLocation
        Source location for lexer.
    """

    cur_loc: SourceLocation = SourceLocation(0, 0)
    cur_tok: Token
    lex_loc: SourceLocation = SourceLocation(0, 0)
    last_char: str = ""
    new_line: bool = True

    _keyword_map = {
        "fn": TokenKind.kw_function,
        "extern": TokenKind.kw_extern,
        "if": TokenKind.kw_if,
        "then": TokenKind.kw_then,
        "else": TokenKind.kw_else,
        "for": TokenKind.kw_for,
        "in": TokenKind.kw_in,
        "var": TokenKind.kw_var,
        "const": TokenKind.kw_const,
    }

    @classmethod
    def gettok(cls) -> Token:
        """
        Get the next token.

        Returns
        -------
        int
            The next token from standard input.
        """
        if cls.last_char == "":
            cls.new_line = True
            cls.last_char = cls.advance()

        # Skip any whitespace.
        indent = 0
        while cls.last_char.isspace():
            if cls.new_line:
                indent += 1

            if cls.last_char == "\n":
                # note: if it is an empty line it is not necessary to keep
                #       the record about the indentation
                cls.new_line = True
                indent = 0

            cls.last_char = cls.advance()

        cls.new_line = False

        if indent:
            return Token(kind=TokenKind.indent, value=indent)

        Lexer.cur_loc = Lexer.lex_loc

        if cls.last_char.isalpha() or cls.last_char == "_":
            # Identifier
            identifier = cls.last_char
            cls.last_char = cls.advance()

            while cls.last_char.isalnum() or cls.last_char == "_":
                identifier += cls.last_char
                cls.last_char = cls.advance()

            if identifier in cls._keyword_map:
                return Token(
                    kind=cls._keyword_map[identifier], value=identifier
                )

            return Token(kind=TokenKind.identifier, value=identifier)

        # Number: [0-9.]+
        if cls.last_char.isdigit() or cls.last_char == ".":
            num_str = ""
            while cls.last_char.isdigit() or cls.last_char == ".":
                num_str += cls.last_char
                cls.last_char = cls.advance()

            return Token(kind=TokenKind.float_literal, value=float(num_str))

        # Comment until end of line.
        if cls.last_char == "#":
            while (
                cls.last_char != EOF
                and cls.last_char != "\n"
                and cls.last_char != "\r"
            ):
                cls.last_char = cls.advance()

            if cls.last_char != EOF:
                return cls.gettok()

        # Check for end of file. Don't eat the EOF.
        if cls.last_char:
            this_char = cls.last_char
            cls.last_char = cls.advance()
            return Token(kind=TokenKind.operator, value=this_char)
        return Token(kind=TokenKind.eof, value="")

    @classmethod
    def advance(cls) -> str:
        """
        Advance the token from the buffer.

        Returns
        -------
        int
            TokenKind in integer form.
        """
        last_char = ArxIO.get_char()

        if last_char == "\n" or last_char == "\r":
            cls.lex_loc.line += 1
            cls.lex_loc.col = 0
        else:
            cls.lex_loc.col += 1

        return last_char

    @classmethod
    def get_next_token(cls) -> Token:
        """
        Provide a simple token buffer.

        Returns
        -------
        int
            The current token the parser is looking at.
            Reads another token from the lexer and updates
            cur_tok with its results.
        """
        Lexer.cur_tok = cls.gettok()
        return Lexer.cur_tok
