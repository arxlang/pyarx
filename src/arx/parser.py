"""parser module gather all functions and classes for parsing."""
from typing import Dict, List, Optional, Tuple

from arx import ast
from arx.lexer import Lexer, SourceLocation, TokenKind, Token, Any
from arx.logs import LogError


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

    @classmethod
    def parse(cls) -> Optional[ast.TreeAST]:
        """
        Parse the input code.

        Returns
        -------
        Optional[ast.TreeAST]
            The parsed abstract syntax tree (AST), or None if parsing fails.
        """
        tree: ast.TreeAST = ast.TreeAST()
        Lexer.get_next_token()

        while True:
            if Lexer.cur_tok.kind == TokenKind.eof:
                return tree
            elif Lexer.cur_tok.kind == TokenKind.not_initialized:
                Lexer.get_next_token()
            elif Lexer.cur_tok == Token(kind=TokenKind.operator, value=";"):
                Lexer.get_next_token()
                # ignore top-level semicolons.
            elif Lexer.cur_tok.kind == TokenKind.kw_function:
                tree.nodes.append(cls.parse_definition())
            elif Lexer.cur_tok.kind == TokenKind.kw_extern:
                tree.nodes.append(cls.parse_extern())
            else:
                tree.nodes.append(cls.parse_top_level_expr())

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
    def parse_definition(cls) -> Optional[ast.FunctionAST]:
        """
        Parse the function definition expression.

        Returns
        -------
        Optional[ast.FunctionAST]
            The parsed function definition, or None if parsing fails.
        """
        Lexer.get_next_token()  # eat function.
        proto: Optional[ast.PrototypeAST] = cls.parse_prototype()
        if not proto:
            return None

        expression: Optional[ast.ExprAST] = cls.parse_expression()
        if expression:
            return ast.FunctionAST(proto, expression)
        return None

    @classmethod
    def parse_extern(cls) -> Optional[ast.PrototypeAST]:
        """
        Parse the extern expression.

        Returns
        -------
        Optional[ast.PrototypeAST]
            The parsed extern expression as a prototype, or None if parsing
            fails.
        """
        Lexer.get_next_token()  # eat extern.
        return cls.parse_extern_prototype()

    @classmethod
    def parse_top_level_expr(cls) -> Optional[ast.FunctionAST]:
        """
        Parse the top level expression.

        Returns
        -------
        Optional[ast.FunctionAST]
            The parsed top level expression as a function, or None if parsing
            fails.
        """
        fn_loc: SourceLocation = Lexer.cur_loc
        if expr := cls.parse_expression():
            # Make an anonymous proto.
            proto = ast.PrototypeAST(fn_loc, "__anon_expr", "float", [])
            return ast.FunctionAST(proto, expr)
        return None

    @classmethod
    def parse_primary(cls) -> Optional[ast.ExprAST]:
        """
        Parse the primary expression.

        Returns
        -------
        Optional[ast.ExprAST]
            The parsed primary expression, or None if parsing fails.
        """
        msg: str = ""

        if Lexer.cur_tok.kind == TokenKind.identifier:
            return cls.parse_identifier_expr()
        elif Lexer.cur_tok.kind == TokenKind.float_literal:
            return cls.parse_float_expr()
        elif Lexer.cur_tok == Token(kind=TokenKind.operator, value="("):
            return cls.parse_paren_expr()
        elif Lexer.cur_tok.kind == TokenKind.kw_if:
            return cls.parse_if_expr()
        elif Lexer.cur_tok.kind == TokenKind.kw_for:
            return cls.parse_for_expr()
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
        else:
            msg = (
                "Parser: Unknown token when expecting an expression:"
                f"'{Lexer.cur_tok.get_name()}'."
            )
            Lexer.get_next_token()  # eat unknown token
            return LogError(msg)

    @classmethod
    def parse_expression(cls) -> Optional[ast.ExprAST]:
        """
        Parse an expression.

        Returns
        -------
        Optional[ast.ExprAST]
            The parsed expression, or None if parsing fails.
        """
        lhs: Optional[ast.ExprAST] = cls.parse_unary()
        if not lhs:
            return None

        return cls.parse_bin_op_rhs(0, lhs)

    @classmethod
    def parse_if_expr(cls) -> Optional[ast.IfExprAST]:
        """
        Parse the `if` expression.

        Returns
        -------
        Optional[ast.IfExprAST]
            The parsed `if` expression, or None if parsing fails.
        """
        if_loc: SourceLocation = Lexer.cur_loc

        Lexer.get_next_token()  # eat the if.

        cond: Optional[ast.ExprAST] = cls.parse_expression()
        if not cond:
            return None

        if Lexer.cur_tok != Token(kind=TokenKind.operator, value=":"):
            msg = (
                "Parser: `if` statement expected ':', received: '"
                + str(Lexer.cur_tok)
                + "'."
            )
            return LogError(msg)

        Lexer.get_next_token()  # eat the ':'

        then_expr: Optional[ast.ExprAST] = cls.parse_expression()
        if not then_expr:
            return None

        if Lexer.cur_tok.kind != TokenKind.kw_else:
            return LogError("Parser: Expected else")

        Lexer.get_next_token()  # eat the else token

        if Lexer.cur_tok != Token(kind=TokenKind.operator, value=":"):
            msg = (
                "Parser: `else` statement expected ':', received: '"
                + str(Lexer.cur_tok)
                + "'."
            )
            return LogError(msg)

        Lexer.get_next_token()  # eat the ':'

        else_expr: Optional[ast.ExprAST] = cls.parse_expression()
        if not else_expr:
            return None

        return ast.IfExprAST(if_loc, cond, then_expr, else_expr)

    @classmethod
    def parse_float_expr(cls) -> Optional[ast.FloatExprAST]:
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
    def parse_paren_expr(cls) -> Optional[ast.ExprAST]:
        """
        Parse the parenthesis expression.

        Returns
        -------
        ast.ExprAST
            The parsed expression.
        """
        Lexer.get_next_token()  # eat (.
        expr = cls.parse_expression()
        if not expr:
            return None

        if Lexer.cur_tok != Token(kind=TokenKind.operator, value=")"):
            return LogError("Parser: Expected ')'")
        Lexer.get_next_token()  # eat ).
        return expr

    @classmethod
    def parse_identifier_expr(cls) -> Optional[ast.ExprAST]:
        """
        Parse the identifier expression.

        Returns
        -------
        Optional[ast.ExprAST]
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
                arg: Optional[ast.ExprAST] = cls.parse_expression()
                if arg:
                    args.append(arg)
                else:
                    return None

                if Lexer.cur_tok == Token(kind=TokenKind.operator, value=")"):
                    break

                if Lexer.cur_tok != Token(kind=TokenKind.operator, value=","):
                    return LogError(
                        "Parser: Expected ')' or ',' in argument list"
                    )
                Lexer.get_next_token()

        # Eat the ')'.
        Lexer.get_next_token()

        return ast.CallExprAST(id_loc, id_name, args)

    @classmethod
    def parse_for_expr(cls) -> Optional[ast.ForExprAST]:
        """
        Parse the `for` expression.

        Returns
        -------
        Optional[ast.ForExprAST]
            The parsed `for` expression, or None if parsing fails.
        """
        Lexer.get_next_token()  # eat the for.

        if Lexer.cur_tok.kind != TokenKind.identifier:
            return LogError("Parser: Expected identifier after for")

        id_name: str = Lexer.cur_tok.value
        Lexer.get_next_token()  # eat identifier.

        if Lexer.cur_tok != Token(kind=TokenKind.operator, value="="):
            return LogError("Parser: Expected '=' after for")
        Lexer.get_next_token()  # eat '='.

        start: Optional[ast.ExprAST] = cls.parse_expression()
        if not start:
            return None
        if Lexer.cur_tok != Token(kind=TokenKind.operator, value=","):
            return LogError("Parser: Expected ',' after for start value")
        Lexer.get_next_token()

        end: Optional[ast.ExprAST] = cls.parse_expression()
        if not end:
            return None

        # The step value is optional. #
        step: Optional[ast.ExprAST] = None
        if Lexer.cur_tok == Token(kind=TokenKind.operator, value=","):
            Lexer.get_next_token()
            step = cls.parse_expression()
            if not step:
                return None

        if Lexer.cur_tok.kind != TokenKind.kw_in:
            return LogError("Parser: Expected 'in' after for")
        Lexer.get_next_token()  # eat 'in'.

        body: Optional[ast.ExprAST] = cls.parse_expression()
        if not body:
            return None

        return ast.ForExprAST(id_name, start, end, step, body)

    @classmethod
    def parse_var_expr(cls) -> Optional[ast.VarExprAST]:
        """
        Parse the `var` declaration expression.

        Returns
        -------
        Optional[ast.VarExprAST]
            The parsed `var` expression, or None if parsing fails.
        """
        Lexer.get_next_token()  # eat the var.

        var_names: List[Tuple[str, Optional[ast.ExprAST]]] = []

        # At least one variable name is required. #
        if Lexer.cur_tok.kind != TokenKind.identifier:
            return LogError("Parser: Expected identifier after var")

        while True:
            name: str = Lexer.cur_tok.value
            Lexer.get_next_token()  # eat identifier.

            # Read the optional initializer. #
            Init: Optional[ast.ExprAST] = None
            if Lexer.cur_tok == Token(kind=TokenKind.operator, value="="):
                Lexer.get_next_token()  # eat the '='.

                Init = cls.parse_expression()
                if not Init:
                    return None

            var_names.append((name, Init))

            # end of var list, exit loop. #
            if Lexer.cur_tok != Token(kind=TokenKind.operator, value=","):
                break
            Lexer.get_next_token()  # eat the ','.

            if Lexer.cur_tok.kind != TokenKind.identifier:
                return LogError("Parser: Expected identifier list after var")

        # At this point, we have to have 'in'. #
        if Lexer.cur_tok.kind != TokenKind.kw_in:
            return LogError("Parser: Expected 'in' keyword after 'var'")
        Lexer.get_next_token()  # eat 'in'.

        body: Optional[ast.ExprAST] = cls.parse_expression()
        if not body:
            return None

        return ast.VarExprAST(var_names, "float", body)

    @classmethod
    def parse_unary(cls) -> Optional[ast.ExprAST]:
        """
        Parse a unary expression.

        Returns
        -------
        Optional[ast.ExprAST]
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
        operand: Optional[ast.ExprAST] = cls.parse_unary()
        return ast.UnaryExprAST(op_code, operand)

    @classmethod
    def parse_bin_op_rhs(
        cls,
        expr_prec: int,
        lhs: ast.ExprAST,
    ) -> Optional[ast.ExprAST]:
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
        Optional[ast.ExprAST]
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
            rhs: Optional[ast.ExprAST] = cls.parse_unary()
            if not rhs:
                return None

            # If BinOp binds less tightly with rhs than the operator after
            # rhs, let the pending operator take rhs as its lhs
            next_prec: int = cls.get_tok_precedence()
            if cur_prec < next_prec:
                rhs = cls.parse_bin_op_rhs(cur_prec + 1, rhs)
                if not rhs:
                    return None

            # Merge lhs/rhs.
            lhs = ast.BinaryExprAST(bin_loc, bin_op, lhs, rhs)

    @classmethod
    def parse_prototype(cls) -> Optional[ast.PrototypeAST]:
        """
        Parse the prototype expression.

        Returns
        -------
        Optional[ast.PrototypeAST]
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
            return LogError("Parser: Expected function name in prototype")

        if Lexer.cur_tok != Token(kind=TokenKind.operator, value="("):
            return LogError("Parser: Expected '(' in the function definition.")

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
            return LogError("Parser: Expected ')' in the function definition.")

        # success. #
        Lexer.get_next_token()  # eat ')'.

        ret_typing = "float"

        if Lexer.cur_tok != Token(kind=TokenKind.operator, value=":"):
            return LogError("Parser: Expected ':' in the function definition")

        Lexer.get_next_token()  # eat ':'.

        return ast.PrototypeAST(fn_loc, fn_name, ret_typing, args)

    @classmethod
    def parse_extern_prototype(cls) -> Optional[ast.PrototypeAST]:
        """
        Parse an extern prototype expression.

        Returns
        -------
        Optional[ast.PrototypeAST]
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
            return LogError("Parser: Expected function name in prototype")

        if Lexer.cur_tok != Token(kind=TokenKind.operator, value="("):
            return LogError("Parser: Expected '(' in the function definition.")

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
            return LogError("Parser: Expected ')' in the function definition.")

        # success. #
        Lexer.get_next_token()  # eat ')'.

        ret_typing = "float"

        return ast.PrototypeAST(fn_loc, fn_name, ret_typing, args)

    @classmethod
    def parse_return_function(cls) -> Optional[ast.ReturnExprAST]:
        """
        Parse the return expression.

        Returns
        -------
        Optional[ast.ReturnExprAST]
            The parsed return expression, or None if parsing fails.
        """
        Lexer.get_next_token()  # eat return
        return ast.ReturnExprAST(cls.parse_primary())
