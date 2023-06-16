"""Module for handling the lexer analysis."""
from typing import Union

from arx.io import ArxIO

EOF = ""


class Token:
    """
    Token enumeration for known variables returned by the lexer.

    Attributes
    ----------
    tok_eof : int
        End-of-file token.
    tok_function : int
        Function token.
    tok_extern : int
        Extern token.
    tok_return : int
        Return token.
    tok_identifier : int
        Identifier token.
    tok_float_literal : int
        Float literal token.
    tok_if : int
        If token.
    tok_then : int
        Then token.
    tok_else : int
        Else token.
    tok_for : int
        For token.
    tok_in : int
        In token.
    tok_binary : int
        Binary operator token.
    tok_unary : int
        Unary operator token.
    tok_var : int
        Variable definition token.
    tok_const : int
        Constant token.
    tok_not_initialized : int
        Not initialized token.
    """

    tok_eof: int = -1
    tok_function: int = -2
    tok_extern: int = -3
    tok_return: int = -4
    tok_identifier: int = -10
    tok_float_literal: int = -11
    tok_if: int = -20
    tok_then: int = -21
    tok_else: int = -22
    tok_for: int = -23
    tok_in: int = -24
    tok_binary: int = -30
    tok_unary: int = -31
    tok_var: int = -40
    tok_const: int = -41
    tok_not_initialized: int = -9999


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


class Lexer:
    """
    Lexer class for tokenizing known variables.

    Attributes
    ----------
    cur_loc : SourceLocation
        Current source location.
    identifier_str : str
        Filled in if tok_identifier.
    num_float : float
        Filled in if tok_float_literal.
    cur_tok : int
        Current token.
    lex_loc : SourceLocation
        Source location for lexer.
    """

    cur_loc: SourceLocation = SourceLocation(0, 0)
    identifier_str: str = ""
    num_float: float = 0
    cur_tok: int = 0
    lex_loc: SourceLocation = SourceLocation(0, 0)
    last_char: str = ""

    @classmethod
    def get_tok_name(cls, tok: Union[int, str]) -> str:
        """
        Get the name of the specified token.

        Parameters
        ----------
        tok : int
            Token value.

        Returns
        -------
        str
            Name of the token.
        """
        if tok == Token.tok_eof:
            return "eof"
        elif tok == Token.tok_function:
            return "function"
        elif tok == Token.tok_return:
            return "return"
        elif tok == Token.tok_extern:
            return "extern"
        elif tok == Token.tok_identifier:
            return "identifier"
        elif tok == Token.tok_float_literal:
            return "float"
        elif tok == Token.tok_if:
            return "if"
        elif tok == Token.tok_then:
            return "then"
        elif tok == Token.tok_else:
            return "else"
        elif tok == Token.tok_for:
            return "for"
        elif tok == Token.tok_in:
            return "in"
        elif tok == Token.tok_binary:
            return "binary"
        elif tok == Token.tok_unary:
            return "unary"
        elif tok == Token.tok_var:
            return "var"
        elif tok == Token.tok_const:
            return "const"
        else:
            return tok

    @classmethod
    def gettok(cls) -> int:
        """
        Get the next token.

        Returns
        -------
        int
            The next token from standard input.
        """
        if cls.last_char == "":
            cls.last_char = cls.advance()

        # Skip any whitespace.
        while cls.last_char.isspace():
            cls.last_char = cls.advance()

        Lexer.cur_loc = Lexer.lex_loc

        if cls.last_char.isalpha() or cls.last_char == "_":
            # Identifier
            Lexer.identifier_str = cls.last_char
            cls.last_char = cls.advance()

            while cls.last_char.isalnum() or cls.last_char == "_":
                Lexer.identifier_str += cls.last_char
                cls.last_char = cls.advance()

            if Lexer.identifier_str == "fn":
                return Token.tok_function
            if Lexer.identifier_str == "return":
                return Token.tok_return
            if Lexer.identifier_str == "extern":
                return Token.tok_extern
            if Lexer.identifier_str == "if":
                return Token.tok_if
            if Lexer.identifier_str == "else":
                return Token.tok_else
            if Lexer.identifier_str == "for":
                return Token.tok_for
            if Lexer.identifier_str == "in":
                return Token.tok_in
            if Lexer.identifier_str == "binary":
                return Token.tok_binary
            if Lexer.identifier_str == "unary":
                return Token.tok_unary
            if Lexer.identifier_str == "var":
                return Token.tok_var
            return Token.tok_identifier

        # Number: [0-9.]+
        if cls.last_char.isdigit() or cls.last_char == ".":
            num_str = ""
            while cls.last_char.isdigit() or cls.last_char == ".":
                num_str += cls.last_char
                cls.last_char = cls.advance()

            Lexer.num_float = float(num_str)
            return Token.tok_float_literal

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
        if cls.last_char == EOF:
            return Token.tok_eof

        this_char = cls.last_char
        cls.last_char = cls.advance()
        return this_char

    @classmethod
    def advance(cls) -> str:
        """
        Advance the token from the buffer.

        Returns
        -------
        int
            Token in integer form.
        """
        last_char = ArxIO.get_char()

        if last_char == "\n" or last_char == "\r":
            cls.lex_loc.line += 1
            cls.lex_loc.col = 0
        else:
            cls.lex_loc.col += 1

        return last_char

    @classmethod
    def get_next_token(cls) -> int:
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


def get_token_value(tok: int) -> str:
    """
    Return the string representation of a token value.

    Parameters
    ----------
        tok (int): The token value.

    Returns
    -------
        str: The string representation of the token value.
    """
    if tok == Token.tok_identifier:
        return "(" + Lexer.identifier_str + ")"
    elif tok == Token.tok_float_literal:
        return "(" + str(Lexer.num_float) + ")"
    else:
        return ""
