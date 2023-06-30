"""parser module gather all functions and classes for parsing."""
from typing import Dict, List, Tuple

from arx import ast
from arx.exceptions import ParserException
from arx.lexer import Lexer, SourceLocation, TokenKind, Token

INDENT_SIZE = 2


class Parser:
    """Parser class."""

    bin_op_precedence: Dict[str, int] = {
        "=": 2,
        "<": 10,
        ">": 10,
        "+": 20,
        "-": 20,
        "*": 40,
    }

    indent_level: int = 0

    @classmethod
    def reset(cls):
        """Reset the Parser static variables."""
        cls.indent_level = 0

    @classmethod
    def parse(cls) -> ast.BlockAST:
        """
        Parse the input code.

        Returns
        -------
        ast.BlockAST
            The parsed abstract syntax tree (AST), or None if parsing fails.
        """
        cls.reset()

        tree: ast.BlockAST = ast.BlockAST()
        Lexer.get_next_token()

        if Lexer.cur_tok.kind == TokenKind.not_initialized:
            Lexer.get_next_token()

        while True:
            if Lexer.cur_tok.kind == TokenKind.eof:
                break
            elif Lexer.cur_tok == Token(kind=TokenKind.operator, value=";"):
                # ignore top-level semicolons.
                Lexer.get_next_token()
            elif Lexer.cur_tok.kind == TokenKind.kw_function:
                tree.nodes.append(cls.parse_definition())
            elif Lexer.cur_tok.kind == TokenKind.kw_extern:
                tree.nodes.append(cls.parse_extern())
            else:
                tree.nodes.append(cls.parse_expression())

        return tree

    @classmethod
    def get_tok_precedence(cls) -> int:
        """
        Get the precedence of the pending binary operator token.

        Returns
        -------
        int
            The token precedence.
        """
        return cls.bin_op_precedence.get(Lexer.cur_tok.value, -1)

    @classmethod
    def parse_definition(cls) -> ast.FunctionAST:
        """
        Parse the function definition expression.

        Returns
        -------
        ast.FunctionAST
            The parsed function definition, or None if parsing fails.
        """
        Lexer.get_next_token()  # eat function.
        proto: ast.PrototypeAST = cls.parse_prototype()

        return ast.FunctionAST(proto, cls.parse_block())

    @classmethod
    def parse_extern(cls) -> ast.PrototypeAST:
        """
        Parse the extern expression.

        Returns
        -------
        ast.PrototypeAST
            The parsed extern expression as a prototype, or None if parsing
            fails.
        """
        Lexer.get_next_token()  # eat extern.
        return cls.parse_extern_prototype()

    @classmethod
    def parse_primary(cls) -> ast.ExprAST:
        """
        Parse the primary expression.

        Returns
        -------
        ast.ExprAST
            The parsed primary expression, or None if parsing fails.
        """
        if Lexer.cur_tok.kind == TokenKind.identifier:
            return cls.parse_identifier_expr()
        elif Lexer.cur_tok.kind == TokenKind.float_literal:
            return cls.parse_float_expr()
        elif Lexer.cur_tok == Token(kind=TokenKind.operator, value="("):
            return cls.parse_paren_expr()
        elif Lexer.cur_tok.kind == TokenKind.kw_if:
            return cls.parse_if_stmt()
        elif Lexer.cur_tok.kind == TokenKind.kw_for:
            return cls.parse_for_stmt()
        elif Lexer.cur_tok.kind == TokenKind.kw_var:
            return cls.parse_var_expr()
        elif Lexer.cur_tok == Token(kind=TokenKind.operator, value=";"):
            # ignore top-level semicolons.
            Lexer.get_next_token()  # eat `;`
            return cls.parse_primary()
        elif Lexer.cur_tok.kind == TokenKind.kw_return:
            # ignore return for now
            Lexer.get_next_token()  # eat kw_return
            return cls.parse_primary()
        elif Lexer.cur_tok.kind == TokenKind.indent:
            return cls.parse_block()
        else:
            msg: str = (
                "Parser: Unknown token when expecting an expression:"
                f"'{Lexer.cur_tok.get_name()}'."
            )
            Lexer.get_next_token()  # eat unknown token
            raise Exception(msg)

    @classmethod
    def parse_block(cls) -> ast.BlockAST:
        """Parse a block of nodes."""
        cur_indent: int = Lexer.cur_tok.value

        Lexer.get_next_token()  # eat indentation

        block: ast.BlockAST = ast.BlockAST()

        if cur_indent == cls.indent_level:
            raise ParserException("There is no new block to be parsed.")

        if cur_indent > cls.indent_level:
            cls.indent_level = cur_indent

            while expr := cls.parse_expression():
                block.nodes.append(expr)
                if Lexer.cur_tok.kind != TokenKind.indent:
                    break

                new_indent = Lexer.cur_tok
                Lexer.get_next_token()  # eat indentation
                if new_indent.value < cur_indent:
                    break

        cls.indent_level -= INDENT_SIZE
        return block

    @classmethod
    def parse_expression(cls) -> ast.ExprAST:
        """
        Parse an expression.

        Returns
        -------
        ast.ExprAST
            The parsed expression, or None if parsing fails.
        """
        lhs: ast.ExprAST = cls.parse_unary()
        return cls.parse_bin_op_rhs(0, lhs)

    @classmethod
    def parse_if_stmt(cls) -> ast.IfStmtAST:
        """
        Parse the `if` expression.

        Returns
        -------
        ast.IfStmtAST
            The parsed `if` expression, or None if parsing fails.
        """
        if_loc: SourceLocation = Lexer.cur_loc

        Lexer.get_next_token()  # eat the if.

        cond: ast.ExprAST = cls.parse_expression()

        if Lexer.cur_tok != Token(kind=TokenKind.operator, value=":"):
            msg = (
                "Parser: `if` statement expected ':', received: '"
                + str(Lexer.cur_tok)
                + "'."
            )
            raise Exception(msg)

        Lexer.get_next_token()  # eat the ':'

        then_block: ast.BlockAST = ast.BlockAST()
        else_block: ast.BlockAST = ast.BlockAST()

        then_block = cls.parse_block()

        if Lexer.cur_tok.kind == TokenKind.indent:
            Lexer.get_next_token()  # eat the indentation

        if Lexer.cur_tok.kind == TokenKind.kw_else:
            Lexer.get_next_token()  # eat the else token

            if Lexer.cur_tok != Token(kind=TokenKind.operator, value=":"):
                msg = (
                    "Parser: `else` statement expected ':', received: '"
                    + str(Lexer.cur_tok)
                    + "'."
                )
                raise Exception(msg)

            Lexer.get_next_token()  # eat the ':'
            else_block = cls.parse_block()

        return ast.IfStmtAST(if_loc, cond, then_block, else_block)

    @classmethod
    def parse_float_expr(cls) -> ast.FloatExprAST:
        """
        Parse the number expression.

        Returns
        -------
        ast.FloatExprAST
            The parsed float expression.
        """
        result = ast.FloatExprAST(Lexer.cur_tok.value)
        Lexer.get_next_token()  # consume the number
        return result

    @classmethod
    def parse_paren_expr(cls) -> ast.ExprAST:
        """
        Parse the parenthesis expression.

        Returns
        -------
        ast.ExprAST
            The parsed expression.
        """
        Lexer.get_next_token()  # eat (.
        expr = cls.parse_expression()

        if Lexer.cur_tok != Token(kind=TokenKind.operator, value=")"):
            raise Exception("Parser: Expected ')'")
        Lexer.get_next_token()  # eat ).
        return expr

    @classmethod
    def parse_identifier_expr(cls) -> ast.ExprAST:
        """
        Parse the identifier expression.

        Returns
        -------
        ast.ExprAST
            The parsed expression, or None if parsing fails.
        """
        id_name: str = Lexer.cur_tok.value

        id_loc: SourceLocation = Lexer.cur_loc

        Lexer.get_next_token()  # eat identifier.

        if Lexer.cur_tok != Token(kind=TokenKind.operator, value="("):
            # Simple variable ref, not a function call
            # todo: we need to get the variable type from a specific scope
            return ast.VariableExprAST(id_loc, id_name, "float")

        # Call.
        Lexer.get_next_token()  # eat (
        args: List[ast.ExprAST] = []
        if Lexer.cur_tok != Token(kind=TokenKind.operator, value=")"):
            while True:
                args.append(cls.parse_expression())

                if Lexer.cur_tok == Token(kind=TokenKind.operator, value=")"):
                    break

                if Lexer.cur_tok != Token(kind=TokenKind.operator, value=","):
                    raise Exception(
                        "Parser: Expected ')' or ',' in argument list"
                    )
                Lexer.get_next_token()

        # Eat the ')'.
        Lexer.get_next_token()

        return ast.CallExprAST(id_loc, id_name, args)

    @classmethod
    def parse_for_stmt(cls) -> ast.ForStmtAST:
        """
        Parse the `for` expression.

        Returns
        -------
        ast.ForStmtAST
            The parsed `for` expression, or None if parsing fails.
        """
        Lexer.get_next_token()  # eat the for.

        if Lexer.cur_tok.kind != TokenKind.identifier:
            raise Exception("Parser: Expected identifier after for")

        id_name: str = Lexer.cur_tok.value
        Lexer.get_next_token()  # eat identifier.

        if Lexer.cur_tok != Token(kind=TokenKind.operator, value="="):
            raise Exception("Parser: Expected '=' after for")
        Lexer.get_next_token()  # eat '='.

        start: ast.ExprAST = cls.parse_expression()
        if Lexer.cur_tok != Token(kind=TokenKind.operator, value=","):
            raise Exception("Parser: Expected ',' after for start value")
        Lexer.get_next_token()

        end: ast.ExprAST = cls.parse_expression()

        # The step value is optional
        if Lexer.cur_tok == Token(kind=TokenKind.operator, value=","):
            Lexer.get_next_token()
            step = cls.parse_expression()
        else:
            step = ast.FloatExprAST(1.0)

        if Lexer.cur_tok.kind != TokenKind.kw_in:
            raise Exception("Parser: Expected 'in' after for")
        Lexer.get_next_token()  # eat 'in'.

        body_block: ast.BlockAST = ast.BlockAST()
        body_block.nodes.append(cls.parse_expression())
        return ast.ForStmtAST(id_name, start, end, step, body_block)

    @classmethod
    def parse_var_expr(cls) -> ast.VarExprAST:
        """
        Parse the `var` declaration expression.

        Returns
        -------
        ast.VarExprAST
            The parsed `var` expression, or None if parsing fails.
        """
        Lexer.get_next_token()  # eat the var.

        var_names: List[Tuple[str, ast.ExprAST]] = []

        # At least one variable name is required. #
        if Lexer.cur_tok.kind != TokenKind.identifier:
            raise Exception("Parser: Expected identifier after var")

        while True:
            name: str = Lexer.cur_tok.value
            Lexer.get_next_token()  # eat identifier.

            # Read the optional initializer. #
            Init: ast.ExprAST
            if Lexer.cur_tok == Token(kind=TokenKind.operator, value="="):
                Lexer.get_next_token()  # eat the '='.

                Init = cls.parse_expression()
            else:
                Init = ast.FloatExprAST(0.0)

            var_names.append((name, Init))

            # end of var list, exit loop. #
            if Lexer.cur_tok != Token(kind=TokenKind.operator, value=","):
                break
            Lexer.get_next_token()  # eat the ','.

            if Lexer.cur_tok.kind != TokenKind.identifier:
                raise Exception("Parser: Expected identifier list after var")

        # At this point, we have to have 'in'. #
        if Lexer.cur_tok.kind != TokenKind.kw_in:
            raise Exception("Parser: Expected 'in' keyword after 'var'")
        Lexer.get_next_token()  # eat 'in'.

        body: ast.ExprAST = cls.parse_expression()
        return ast.VarExprAST(var_names, "float", body)

    @classmethod
    def parse_unary(cls) -> ast.ExprAST:
        """
        Parse a unary expression.

        Returns
        -------
        ast.ExprAST
            The parsed unary expression, or None if parsing fails.
        """
        # If the current token is not an operator, it must be a primary expr.
        if (
            Lexer.cur_tok.kind != TokenKind.operator
            or Lexer.cur_tok.value in ("(", ",")
        ):
            return cls.parse_primary()

        # If this is a unary operator, read it.
        op_code: str = Lexer.cur_tok.value
        Lexer.get_next_token()
        operand: ast.ExprAST = cls.parse_unary()
        return ast.UnaryExprAST(op_code, operand)

    @classmethod
    def parse_bin_op_rhs(
        cls,
        expr_prec: int,
        lhs: ast.ExprAST,
    ) -> ast.ExprAST:
        """
        Parse a binary expression.

        Parameters
        ----------
        expr_prec : int
            Expression precedence (deprecated).
        lhs : ast.ExprAST
            Left-hand side expression.

        Returns
        -------
        ast.ExprAST
            The parsed binary expression, or None if parsing fails.
        """
        # If this is a binop, find its precedence. #
        while True:
            cur_prec: int = cls.get_tok_precedence()

            # If this is a binop that binds at least as tightly as the current
            # binop, consume it, otherwise we are done.
            if cur_prec < expr_prec:
                return lhs

            # Okay, we know this is a binop.
            bin_op: str = Lexer.cur_tok.value
            bin_loc: SourceLocation = Lexer.cur_loc
            Lexer.get_next_token()  # eat binop

            # Parse the unary expression after the binary operator.
            rhs: ast.ExprAST = cls.parse_unary()

            # If BinOp binds less tightly with rhs than the operator after
            # rhs, let the pending operator take rhs as its lhs
            next_prec: int = cls.get_tok_precedence()
            if cur_prec < next_prec:
                rhs = cls.parse_bin_op_rhs(cur_prec + 1, rhs)

            # Merge lhs/rhs.
            lhs = ast.BinaryExprAST(bin_loc, bin_op, lhs, rhs)

    @classmethod
    def parse_prototype(cls) -> ast.PrototypeAST:
        """
        Parse the prototype expression.

        Returns
        -------
        ast.PrototypeAST
            The parsed prototype, or None if parsing fails.
        """
        fn_name: str
        var_typing: str
        ret_typing: str
        identifier_name: str

        cur_loc: SourceLocation
        fn_loc: SourceLocation = Lexer.cur_loc

        if Lexer.cur_tok.kind == TokenKind.identifier:
            fn_name = Lexer.cur_tok.value
            Lexer.get_next_token()
        else:
            raise Exception("Parser: Expected function name in prototype")

        if Lexer.cur_tok != Token(kind=TokenKind.operator, value="("):
            raise Exception("Parser: Expected '(' in the function definition.")

        args: List[ast.VariableExprAST] = []
        while Lexer.get_next_token().kind == TokenKind.identifier:
            # note: this is a workaround
            identifier_name = Lexer.cur_tok.value
            cur_loc = Lexer.cur_loc

            var_typing = "float"

            args.append(
                ast.VariableExprAST(cur_loc, identifier_name, var_typing)
            )

            if Lexer.get_next_token() != Token(
                kind=TokenKind.operator, value=","
            ):
                break

        if Lexer.cur_tok != Token(kind=TokenKind.operator, value=")"):
            raise Exception("Parser: Expected ')' in the function definition.")

        # success. #
        Lexer.get_next_token()  # eat ')'.

        ret_typing = "float"

        if Lexer.cur_tok != Token(kind=TokenKind.operator, value=":"):
            raise Exception("Parser: Expected ':' in the function definition")

        Lexer.get_next_token()  # eat ':'.

        return ast.PrototypeAST(fn_loc, fn_name, ret_typing, args)

    @classmethod
    def parse_extern_prototype(cls) -> ast.PrototypeAST:
        """
        Parse an extern prototype expression.

        Returns
        -------
        ast.PrototypeAST
            The parsed extern prototype, or None if parsing fails.
        """
        fn_name: str
        var_typing: str
        ret_typing: str
        identifier_name: str

        cur_loc: SourceLocation
        fn_loc = Lexer.cur_loc

        if Lexer.cur_tok.kind == TokenKind.identifier:
            fn_name = Lexer.cur_tok.value
            Lexer.get_next_token()
        else:
            raise Exception("Parser: Expected function name in prototype")

        if Lexer.cur_tok != Token(kind=TokenKind.operator, value="("):
            raise Exception("Parser: Expected '(' in the function definition.")

        args: List[ast.VariableExprAST] = []
        while Lexer.get_next_token().kind == TokenKind.identifier:
            # note: this is a workaround
            identifier_name = Lexer.cur_tok.value
            cur_loc = Lexer.cur_loc

            var_typing = "float"

            args.append(
                ast.VariableExprAST(cur_loc, identifier_name, var_typing)
            )

            if Lexer.get_next_token() != Token(
                kind=TokenKind.operator, value=","
            ):
                break

        if Lexer.cur_tok != Token(kind=TokenKind.operator, value=")"):
            raise Exception("Parser: Expected ')' in the function definition.")

        # success. #
        Lexer.get_next_token()  # eat ')'.

        ret_typing = "float"

        return ast.PrototypeAST(fn_loc, fn_name, ret_typing, args)

    @classmethod
    def parse_return_function(cls) -> ast.ReturnStmtAST:
        """
        Parse the return expression.

        Returns
        -------
        ast.ReturnStmtAST
            The parsed return expression, or None if parsing fails.
        """
        Lexer.get_next_token()  # eat return
        return ast.ReturnStmtAST(cls.parse_primary())
