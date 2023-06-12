from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Tuple, Union

from llvmlite import ir

from arx.ast import *
from arx.lexer import Lexer, SourceLocation


class Parser:
    bin_op_precedence: Dict[str, int] = {}

    @staticmethod
    def setup():
        Parser.bin_op_precedence["="] = 2
        Parser.bin_op_precedence["<"] = 10
        Parser.bin_op_precedence["+"] = 20
        Parser.bin_op_precedence["-"] = 20
        Parser.bin_op_precedence["*"] = 40

    @staticmethod
    def parse() -> Optional[TreeAST]:
        """
        Parse the input code.

        Returns
        -------
        Optional[TreeAST]
            The parsed abstract syntax tree (AST), or None if parsing fails.
        """
        ast: TreeAST = TreeAST()

        while True:
            if Lexer.cur_tok == tok_eof:
                return ast
            elif Lexer.cur_tok == tok_not_initialized:
                Lexer.get_next_token()
            elif Lexer.cur_tok == ";":
                Lexer.get_next_token()
                # ignore top-level semicolons.
            elif Lexer.cur_tok == tok_function:
                ast.nodes.append(parse_definition())
            elif Lexer.cur_tok == tok_extern:
                ast.nodes.append(parse_extern())
            else:
                ast.nodes.append(parse_top_level_expr())

        return ast

    @staticmethod
    def get_tok_precedence() -> int:
        """
        Get the precedence of the pending binary operator token.

        Returns
        -------
        int
            The token precedence.
        """
        if not Lexer.cur_tok.isascii():
            return -1

        # Make sure it's a declared binop.
        tok_prec: int = Parser.bin_op_precedence.get(Lexer.cur_tok, -1)
        if tok_prec <= 0:
            return -1
        return tok_prec

    @staticmethod
    def parse_definition() -> Optional[FunctionAST]:
        """
        Parse the function definition expression.

        Returns
        -------
        Optional[FunctionAST]
            The parsed function definition, or None if parsing fails.
        """
        Lexer.get_next_token()  # eat function.
        proto: Optional[PrototypeAST] = self.parse_prototype()
        if not proto:
            return None

        expression: Optional[ExprAST] = self.parse_expression()
        if expression:
            return FunctionAST(proto, expression)
        return None

    @staticmethod
    def parse_extern() -> Optional[PrototypeAST]:
        """
        Parse the extern expression.

        Returns
        -------
        Optional[PrototypeAST]
            The parsed extern expression as a prototype, or None if parsing fails.
        """
        Lexer.get_next_token()  # eat extern.
        return parse_extern_prototype()

    @staticmethod
    def parse_top_level_expr() -> Optional[FunctionAST]:
        """
        Parse the top level expression.

        Returns
        -------
        Optional[FunctionAST]
            The parsed top level expression as a function, or None if parsing fails.
        """
        fn_loc: SourceLocation = Lexer.cur_loc
        if expr := self.parse_expression():
            # Make an anonymous proto.
            proto = PrototypeAST(fn_loc, "__anon_expr", "float", [])
            return FunctionAST(proto, expr)
        return None

    @staticmethod
    def parse_primary() -> Optional[ExprAST]:
        """
        Parse the primary expression.

        Returns
        -------
        Optional[ExprAST]
            The parsed primary expression, or None if parsing fails.
        """
        msg: str = ""

        cur_tok = Lexer.cur_tok
        if cur_tok == tok_identifier:
            return Parser.parse_identifier_expr()
        elif cur_tok == tok_float_literal:
            return parse_float_expr()
        elif cur_tok == "(":
            return Parser.parse_paren_expr()
        elif cur_tok == tok_if:
            return parse_if_expr()
        elif cur_tok == tok_for:
            return parse_for_expr()
        elif cur_tok == tok_var:
            return parse_var_expr()
        elif cur_tok == ";":
            # ignore top-level semicolons.
            Lexer.get_next_token()  # eat `;`
            return parse_primary()
        elif cur_tok == tok_return:
            # ignore return for now
            Lexer.get_next_token()  # eat tok_return
            return parse_primary()
        else:
            msg = f"Parser: Unknown token when expecting an expression: '{cur_tok}'."
            Lexer.get_next_token()  # eat unknown token
            return LogError(msg)

    @staticmethod
    def parse_expression() -> Optional[ExprAST]:
        """
        Parse an expression.

        Returns
        -------
        Optional[ExprAST]
            The parsed expression, or None if parsing fails.
        """
        lhs: Optional[ExprAST] = self.parse_unary()
        if not lhs:
            return None

        return parse_bin_op_rhs(0, lhs)

    @staticmethod
    def parse_if_expr() -> Optional[IfExprAST]:
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

        # condition.
        cond: Optional[ExprAST] = self.parse_expression()
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

        then_expr: Optional[ExprAST] = self.parse_expression()
        if not then_expr:
            return None

        if Lexer.cur_tok != tok_else:
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

        else_expr: Optional[ExprAST] = self.parse_expression()
        if not else_expr:
            return None

        return IfExprAST(if_loc, cond, then_expr, else_expr)

    @staticmethod
    def parse_float_expr() -> Optional[FloatExprAST]:
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

    @staticmethod
    def parse_paren_expr() -> Optional[ExprAST]:
        """
        Parse the parenthesis expression.

        Returns
        -------
        ExprAST
            The parsed expression.
        """
        Lexer.get_next_token()  # eat (.
        expr = self.parse_expression()
        if not expr:
            return None

        if Lexer.cur_tok != ")":
            return LogError("Parser: Expected ')'")
        Lexer.get_next_token()  # eat ).
        return expr

    @staticmethod
    def parse_identifier_expr() -> Optional[ExprAST]:
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
                arg: Optional[ExprAST] = self.parse_expression()
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

    @staticmethod
    def parse_for_expr() -> Optional[ForExprAST]:
        """
        Parse the `for` expression.

        Returns
        -------
        Optional[ForExprAST]
            The parsed `for` expression, or None if parsing fails.
        """
        Lexer.get_next_token()  # eat the for.

        if Lexer.cur_tok != tok_identifier:
            return LogError("Parser: Expected identifier after for")

        id_name: str = Lexer.identifier_str
        Lexer.get_next_token()  # eat identifier.

        if Lexer.cur_tok != "=":
            return LogError("Parser: Expected '=' after for")
        Lexer.get_next_token()  # eat '='.

        start: Optional[ExprAST] = self.parse_expression()
        if not start:
            return None
        if Lexer.cur_tok != ",":
            return LogError("Parser: Expected ',' after for start value")
        Lexer.get_next_token()

        end: Optional[ExprAST] = self.parse_expression()
        if not end:
            return None

        # The step value is optional. #
        step: Optional[ExprAST] = None
        if Lexer.cur_tok == ",":
            Lexer.get_next_token()
            step = self.parse_expression()
            if not step:
                return None

        if Lexer.cur_tok != tok_in:
            return LogError("Parser: Expected 'in' after for")
        Lexer.get_next_token()  # eat 'in'.

        body: Optional[ExprAST] = self.parse_expression()
        if not body:
            return None

        return ForExprAST(id_name, start, end, step, body)

    @staticmethod
    def parse_var_expr() -> Optional[VarExprAST]:
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
        if Lexer.cur_tok != tok_identifier:
            return LogError("Parser: Expected identifier after var")

        while True:
            name: str = Lexer.identifier_str
            Lexer.get_next_token()  # eat identifier.

            # Read the optional initializer. #
            Init: Optional[ExprAST] = None
            if Lexer.cur_tok == "=":
                Lexer.get_next_token()  # eat the '='.

                Init = self.parse_expression()
                if not Init:
                    return None

            var_names.append((name, Init))

            # end of var list, exit loop. #
            if Lexer.cur_tok != ",":
                break
            Lexer.get_next_token()  # eat the ','.

            if Lexer.cur_tok != tok_identifier:
                return LogError("Parser: Expected identifier list after var")

        # At this point, we have to have 'in'. #
        if Lexer.cur_tok != tok_in:
            return LogError("Parser: Expected 'in' keyword after 'var'")
        Lexer.get_next_token()  # eat 'in'.

        body: Optional[ExprAST] = self.parse_expression()
        if not body:
            return None

        return VarExprAST(var_names, body)

    @staticmethod
    def parse_unary() -> Optional[ExprAST]:
        """
        Parse a unary expression.

        Returns
        -------
        Optional[ExprAST]
            The parsed unary expression, or None if parsing fails.
        """
        # If the current token is not an operator, it must be a primary expr.
        if (
            not chr(Lexer.cur_tok).isascii()
            or Lexer.cur_tok == "("
            or Lexer.cur_tok == ","
        ):
            return parse_primary()

        # If this is a unary operator, read it.
        op_code: int = Lexer.cur_tok
        Lexer.get_next_token()
        operand: Optional[ExprAST] = self.parse_unary()
        if operand:
            return UnaryExprAST(op_code, operand)
        return None

    @staticmethod
    def parse_bin_op_rhs(
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
            tok_prec: int = self.get_tok_precedence()

            # If this is a binop that binds at least as tightly as the current binop,
            # consume it, otherwise we are done.
            if tok_prec < expr_prec:
                return lhs

            # Okay, we know this is a binop.
            bin_op: int = Lexer.cur_tok
            bin_loc: SourceLocation = Lexer.cur_loc
            Lexer.get_next_token()  # eat binop

            # Parse the unary expression after the binary operator.
            rhs: Optional[ExprAST] = self.parse_unary()
            if not rhs:
                return None

            # If BinOp binds less tightly with rhs than the operator after rhs, let
            # the pending operator take rhs as its lhs.
            next_prec: int = get_tok_precedence()
            if tok_prec < next_prec:
                rhs: Optional[ExprAST] = self.parse_bin_op_rhs(
                    tok_prec + 1, rhs
                )
                if not rhs:
                    return None

            # Merge lhs/rhs.
            lhs: Optional[ExprAST] = BinaryExprAST(bin_loc, bin_op, lhs, rhs)

    @staticmethod
    def parse_prototype() -> Optional[PrototypeAST]:
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

        if Lexer.cur_tok == tok_identifier:
            fn_name = Lexer.identifier_str
            Lexer.get_next_token()
        else:
            return LogError("Parser: Expected function name in prototype")

        if Lexer.cur_tok != "(":
            return LogError("Parser: Expected '(' in the function definition.")

        args: List[VariableExprAST] = []
        while Lexer.get_next_token() == tok_identifier:
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

    @staticmethod
    def parse_extern_prototype() -> Optional[PrototypeAST]:
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

        if Lexer.cur_tok == tok_identifier:
            fn_name = Lexer.identifier_str
            Lexer.get_next_token()
        else:
            return LogError("Parser: Expected function name in prototype")

        if Lexer.cur_tok != "(":
            return LogError("Parser: Expected '(' in the function definition.")

        args: List[VariableExprAST] = []
        while Lexer.get_next_token() == tok_identifier:
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

    @staticmethod
    def parse_return_function() -> Optional[ReturnExprAST]:
        """
        Parse the return expression.

        Returns
        -------
        Optional[ReturnExprAST]
            The parsed return expression, or None if parsing fails.
        """
        Lexer.get_next_token()  # eat return
        return ReturnExprAST(parse_primary())
