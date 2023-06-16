"""parser module gather all functions and classes for parsing."""
from typing import Dict, List, Optional, Tuple

from arx.ast import (
    BinaryExprAST,
    CallExprAST,
    ExprAST,
    FloatExprAST,
    ForExprAST,
    FunctionAST,
    IfExprAST,
    PrototypeAST,
    ReturnExprAST,
    TreeAST,
    UnaryExprAST,
    VarExprAST,
    VariableExprAST,
)
from arx.lexer import Lexer, SourceLocation, Token
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
    def parse(cls) -> Optional[TreeAST]:
        """
        Parse the input code.

        Returns
        -------
        Optional[TreeAST]
            The parsed abstract syntax tree (AST), or None if parsing fails.
        """
        ast: TreeAST = TreeAST()
        Lexer.get_next_token()

        while True:
            if Lexer.cur_tok == Token.tok_eof:
                return ast
            elif Lexer.cur_tok == Token.tok_not_initialized:
                Lexer.get_next_token()
            elif Lexer.cur_tok == ";":
                Lexer.get_next_token()
                # ignore top-level semicolons.
            elif Lexer.cur_tok == Token.tok_function:
                ast.nodes.append(cls.parse_definition())
            elif Lexer.cur_tok == Token.tok_extern:
                ast.nodes.append(cls.parse_extern())
            else:
                ast.nodes.append(cls.parse_top_level_expr())

        return ast

    @classmethod
    def get_tok_precedence(cls) -> int:
        """
        Get the precedence of the pending binary operator token.

        Returns
        -------
        int
            The token precedence.
        """
        if not isinstance(Lexer.cur_tok, str) or not Lexer.cur_tok.isascii():
            return -1

        # Make sure it's a declared binop.
        tok_prec: int = cls.bin_op_precedence.get(Lexer.cur_tok, -1)
        if tok_prec <= 0:
            return -1
        return tok_prec

    @classmethod
    def parse_definition(cls) -> Optional[FunctionAST]:
        """
        Parse the function definition expression.

        Returns
        -------
        Optional[FunctionAST]
            The parsed function definition, or None if parsing fails.
        """
        Lexer.get_next_token()  # eat function.
        proto: Optional[PrototypeAST] = cls.parse_prototype()
        if not proto:
            return None

        expression: Optional[ExprAST] = cls.parse_expression()
        if expression:
            return FunctionAST(proto, expression)
        return None

    @classmethod
    def parse_extern(cls) -> Optional[PrototypeAST]:
        """
        Parse the extern expression.

        Returns
        -------
        Optional[PrototypeAST]
            The parsed extern expression as a prototype, or None if parsing
            fails.
        """
        Lexer.get_next_token()  # eat extern.
        return cls.parse_extern_prototype()

    @classmethod
    def parse_top_level_expr(cls) -> Optional[FunctionAST]:
        """
        Parse the top level expression.

        Returns
        -------
        Optional[FunctionAST]
            The parsed top level expression as a function, or None if parsing
            fails.
        """
        fn_loc: SourceLocation = Lexer.cur_loc
        if expr := cls.parse_expression():
            # Make an anonymous proto.
            proto = PrototypeAST(fn_loc, "__anon_expr", "float", [])
            return FunctionAST(proto, expr)
        return None

    @classmethod
    def parse_primary(cls) -> Optional[ExprAST]:
        """
        Parse the primary expression.

        Returns
        -------
        Optional[ExprAST]
            The parsed primary expression, or None if parsing fails.
        """
        msg: str = ""

        cur_tok = Lexer.cur_tok
        if cur_tok == Token.tok_identifier:
            return cls.parse_identifier_expr()
        elif cur_tok == Token.tok_float_literal:
            return cls.parse_float_expr()
        elif cur_tok == "(":
            return cls.parse_paren_expr()
        elif cur_tok == Token.tok_if:
            return cls.parse_if_expr()
        elif cur_tok == Token.tok_for:
            return cls.parse_for_expr()
        elif cur_tok == Token.tok_var:
            return cls.parse_var_expr()
        elif cur_tok == ";":
            # ignore top-level semicolons.
            Lexer.get_next_token()  # eat `;`
            return cls.parse_primary()
        elif cur_tok == Token.tok_return:
            # ignore return for now
            Lexer.get_next_token()  # eat tok_return
            return cls.parse_primary()
        else:
            msg = (
                "Parser: Unknown token when expecting an expression:"
                f"'{cur_tok}'."
            )
            Lexer.get_next_token()  # eat unknown token
            return LogError(msg)

    @classmethod
    def parse_expression(cls) -> Optional[ExprAST]:
        """
        Parse an expression.

        Returns
        -------
        Optional[ExprAST]
            The parsed expression, or None if parsing fails.
        """
        lhs: Optional[ExprAST] = cls.parse_unary()
        if not lhs:
            return None

        return cls.parse_bin_op_rhs(0, lhs)

    @classmethod
    def parse_if_expr(cls) -> Optional[IfExprAST]:
        """
        Parse the `if` expression.

        Returns
        -------
        Optional[IfExprAST]
            The parsed `if` expression, or None if parsing fails.
        """
        if_loc: SourceLocation = Lexer.cur_loc
        msg: str = ""

        Lexer.get_next_token()  # eat the if.

        breakpoint()
        cond: Optional[ExprAST] = cls.parse_expression()
        if not cond:
            return None

        if Lexer.cur_tok != ":":
            msg = (
                "Parser: `if` statement expected ':', received: '"
                + str(Lexer.cur_tok)
                + "'."
            )
            return LogError(msg)

        Lexer.get_next_token()  # eat the ':'

        then_expr: Optional[ExprAST] = cls.parse_expression()
        if not then_expr:
            return None

        if Lexer.cur_tok != Token.tok_else:
            return LogError("Parser: Expected else")

        Lexer.get_next_token()  # eat the else token

        if Lexer.cur_tok != ":":
            msg = (
                "Parser: `else` statement expected ':', received: '"
                + str(Lexer.cur_tok)
                + "'."
            )
            return LogError(msg)

        Lexer.get_next_token()  # eat the ':'

        else_expr: Optional[ExprAST] = cls.parse_expression()
        if not else_expr:
            return None

        return IfExprAST(if_loc, cond, then_expr, else_expr)

    @classmethod
    def parse_float_expr(cls) -> Optional[FloatExprAST]:
        """
        Parse the number expression.

        Returns
        -------
        FloatExprAST
            The parsed float expression.
        """
        result = FloatExprAST(Lexer.num_float)
        Lexer.get_next_token()  # consume the number
        return result

    @classmethod
    def parse_paren_expr(cls) -> Optional[ExprAST]:
        """
        Parse the parenthesis expression.

        Returns
        -------
        ExprAST
            The parsed expression.
        """
        Lexer.get_next_token()  # eat (.
        expr = cls.parse_expression()
        if not expr:
            return None

        if Lexer.cur_tok != ")":
            return LogError("Parser: Expected ')'")
        Lexer.get_next_token()  # eat ).
        return expr

    @classmethod
    def parse_identifier_expr(cls) -> Optional[ExprAST]:
        """
        Parse the identifier expression.

        Returns
        -------
        Optional[ExprAST]
            The parsed expression, or None if parsing fails.
        """
        id_name: str = Lexer.identifier_str

        id_loc: SourceLocation = Lexer.cur_loc

        Lexer.get_next_token()  # eat identifier.

        if Lexer.cur_tok != "(":
            # Simple variable ref, not a function call
            # todo: we need to get the variable type from a specific scope
            return VariableExprAST(id_loc, id_name, "float")

        # Call.
        Lexer.get_next_token()  # eat (
        args: List[ExprAST] = []
        if Lexer.cur_tok != ")":
            while True:
                arg: Optional[ExprAST] = cls.parse_expression()
                if arg:
                    args.append(arg)
                else:
                    return None

                if Lexer.cur_tok == ")":
                    break

                if Lexer.cur_tok != ",":
                    return LogError(
                        "Parser: Expected ')' or ',' in argument list"
                    )
                Lexer.get_next_token()

        # Eat the ')'.
        Lexer.get_next_token()

        return CallExprAST(id_loc, id_name, args)

    @classmethod
    def parse_for_expr(cls) -> Optional[ForExprAST]:
        """
        Parse the `for` expression.

        Returns
        -------
        Optional[ForExprAST]
            The parsed `for` expression, or None if parsing fails.
        """
        Lexer.get_next_token()  # eat the for.

        if Lexer.cur_tok != Token.tok_identifier:
            return LogError("Parser: Expected identifier after for")

        id_name: str = Lexer.identifier_str
        Lexer.get_next_token()  # eat identifier.

        if Lexer.cur_tok != "=":
            return LogError("Parser: Expected '=' after for")
        Lexer.get_next_token()  # eat '='.

        start: Optional[ExprAST] = cls.parse_expression()
        if not start:
            return None
        if Lexer.cur_tok != ",":
            return LogError("Parser: Expected ',' after for start value")
        Lexer.get_next_token()

        end: Optional[ExprAST] = cls.parse_expression()
        if not end:
            return None

        # The step value is optional. #
        step: Optional[ExprAST] = None
        if Lexer.cur_tok == ",":
            Lexer.get_next_token()
            step = cls.parse_expression()
            if not step:
                return None

        if Lexer.cur_tok != Token.tok_in:
            return LogError("Parser: Expected 'in' after for")
        Lexer.get_next_token()  # eat 'in'.

        body: Optional[ExprAST] = cls.parse_expression()
        if not body:
            return None

        return ForExprAST(id_name, start, end, step, body)

    @classmethod
    def parse_var_expr(cls) -> Optional[VarExprAST]:
        """
        Parse the `var` declaration expression.

        Returns
        -------
        Optional[VarExprAST]
            The parsed `var` expression, or None if parsing fails.
        """
        Lexer.get_next_token()  # eat the var.

        var_names: List[Tuple[str, Optional[ExprAST]]] = []

        # At least one variable name is required. #
        if Lexer.cur_tok != Token.tok_identifier:
            return LogError("Parser: Expected identifier after var")

        while True:
            name: str = Lexer.identifier_str
            Lexer.get_next_token()  # eat identifier.

            # Read the optional initializer. #
            Init: Optional[ExprAST] = None
            if Lexer.cur_tok == "=":
                Lexer.get_next_token()  # eat the '='.

                Init = cls.parse_expression()
                if not Init:
                    return None

            var_names.append((name, Init))

            # end of var list, exit loop. #
            if Lexer.cur_tok != ",":
                break
            Lexer.get_next_token()  # eat the ','.

            if Lexer.cur_tok != Token.tok_identifier:
                return LogError("Parser: Expected identifier list after var")

        # At this point, we have to have 'in'. #
        if Lexer.cur_tok != Token.tok_in:
            return LogError("Parser: Expected 'in' keyword after 'var'")
        Lexer.get_next_token()  # eat 'in'.

        body: Optional[ExprAST] = cls.parse_expression()
        if not body:
            return None

        return VarExprAST(var_names, body)

    @classmethod
    def parse_unary(cls) -> Optional[ExprAST]:
        """
        Parse a unary expression.

        Returns
        -------
        Optional[ExprAST]
            The parsed unary expression, or None if parsing fails.
        """
        # If the current token is not an operator, it must be a primary expr.
        if (
            not isinstance(Lexer.cur_tok, str)
            or Lexer.cur_tok == "("
            or Lexer.cur_tok == ","
        ):
            return cls.parse_primary()

        # If this is a unary operator, read it.
        op_code: int = Lexer.cur_tok
        Lexer.get_next_token()
        operand: Optional[ExprAST] = cls.parse_unary()
        if operand:
            return UnaryExprAST(op_code, operand)
        return None

    @classmethod
    def parse_bin_op_rhs(
        cls,
        expr_prec: int,
        lhs: ExprAST,
    ) -> Optional[ExprAST]:
        """
        Parse a binary expression.

        Parameters
        ----------
        expr_prec : int
            Expression precedence (deprecated).
        lhs : ExprAST
            Left-hand side expression.

        Returns
        -------
        Optional[ExprAST]
            The parsed binary expression, or None if parsing fails.
        """
        # If this is a binop, find its precedence. #
        while True:
            tok_prec: int = cls.get_tok_precedence()

            # If this is a binop that binds at least as tightly as the current
            # binop, consume it, otherwise we are done.
            if tok_prec < expr_prec:
                return lhs

            # Okay, we know this is a binop.
            bin_op: int = Lexer.cur_tok
            bin_loc: SourceLocation = Lexer.cur_loc
            Lexer.get_next_token()  # eat binop

            # Parse the unary expression after the binary operator.
            rhs: Optional[ExprAST] = cls.parse_unary()
            if not rhs:
                return None

            # If BinOp binds less tightly with rhs than the operator after
            # rhs, let the pending operator take rhs as its lhs
            next_prec: int = cls.get_tok_precedence()
            if tok_prec < next_prec:
                rhs: Optional[ExprAST] = cls.parse_bin_op_rhs(
                    tok_prec + 1, rhs
                )
                if not rhs:
                    return None

            # Merge lhs/rhs.
            lhs: Optional[ExprAST] = BinaryExprAST(bin_loc, bin_op, lhs, rhs)

    @classmethod
    def parse_prototype(cls) -> Optional[PrototypeAST]:
        """
        Parse the prototype expression.

        Returns
        -------
        Optional[PrototypeAST]
            The parsed prototype, or None if parsing fails.
        """
        fn_name: str
        var_type_annotation: str
        ret_type_annotation: str
        identifier_name: str

        cur_loc: SourceLocation
        fn_loc: SourceLocation = Lexer.cur_loc

        if Lexer.cur_tok == Token.tok_identifier:
            fn_name = Lexer.identifier_str
            Lexer.get_next_token()
        else:
            return LogError("Parser: Expected function name in prototype")

        if Lexer.cur_tok != "(":
            return LogError("Parser: Expected '(' in the function definition.")

        args: List[VariableExprAST] = []
        while Lexer.get_next_token() == Token.tok_identifier:
            # note: this is a workaround
            identifier_name = Lexer.identifier_str
            cur_loc = Lexer.cur_loc

            var_type_annotation = "float"

            args.append(
                VariableExprAST(cur_loc, identifier_name, var_type_annotation)
            )

            if Lexer.get_next_token() != ",":
                break

        if Lexer.cur_tok != ")":
            return LogError("Parser: Expected ')' in the function definition.")

        # success. #
        Lexer.get_next_token()  # eat ')'.

        ret_type_annotation = "float"

        if Lexer.cur_tok != ":":
            return LogError("Parser: Expected ':' in the function definition")

        Lexer.get_next_token()  # eat ':'.

        return PrototypeAST(fn_loc, fn_name, ret_type_annotation, args)

    @classmethod
    def parse_extern_prototype(cls) -> Optional[PrototypeAST]:
        """
        Parse an extern prototype expression.

        Returns
        -------
        Optional[PrototypeAST]
            The parsed extern prototype, or None if parsing fails.
        """
        fn_name: str
        var_type_annotation: str
        ret_type_annotation: str
        identifier_name: str

        cur_loc: SourceLocation
        fn_loc = Lexer.cur_loc

        if Lexer.cur_tok == Token.tok_identifier:
            fn_name = Lexer.identifier_str
            Lexer.get_next_token()
        else:
            return LogError("Parser: Expected function name in prototype")

        if Lexer.cur_tok != "(":
            return LogError("Parser: Expected '(' in the function definition.")

        args: List[VariableExprAST] = []
        while Lexer.get_next_token() == Token.tok_identifier:
            # note: this is a workaround
            identifier_name = Lexer.identifier_str
            cur_loc = Lexer.cur_loc

            var_type_annotation = "float"

            args.append(
                VariableExprAST(cur_loc, identifier_name, var_type_annotation)
            )

            if Lexer.get_next_token() != ",":
                break

        if Lexer.cur_tok != ")":
            return LogError("Parser: Expected ')' in the function definition.")

        # success. #
        Lexer.get_next_token()  # eat ')'.

        ret_type_annotation = "float"

        return PrototypeAST(fn_loc, fn_name, ret_type_annotation, args)

    @classmethod
    def parse_return_function(cls) -> Optional[ReturnExprAST]:
        """
        Parse the return expression.

        Returns
        -------
        Optional[ReturnExprAST]
            The parsed return expression, or None if parsing fails.
        """
        Lexer.get_next_token()  # eat return
        return ReturnExprAST(cls.parse_primary())
