"""Arx main module."""
from typing import Any, List

from arx.io import ArxIO
from arx.lexer import Lexer
from arx.parser import Parser
from arx.codegen.ast_output import ASTtoOutput
from arx.codegen.file_object import ObjectGenerator


class ArxMain:
    """The main class for calling Arx compiler."""

    input_files: List[str]
    output_file: str
    is_lib: bool

    def run(self, *args: Any, **kwargs: Any) -> None:
        """Compile the given source code."""
        self.input_files = kwargs.get("input_files", [])
        self.output_file = kwargs.get("output_file", "")
        # is_lib now is the only available option
        self.is_lib = kwargs.get("is_lib", True) or True

        if kwargs.get("show_ast"):
            return self.show_ast()

        if kwargs.get("show_tokens"):
            return self.show_tokens()

        if kwargs.get("show_llvm_ir"):
            return self.show_llvm_ir()

        if kwargs.get("shell"):
            return self.run_shell()

        self.compile()

    def show_ast(self) -> None:
        """Print the AST for the given input file."""
        for input_file in self.input_files:
            ArxIO.file_to_buffer(input_file)
            ast = Parser.parse()
            printer = ASTtoOutput()
            printer.emit_ast(ast)

    def show_tokens(self) -> None:
        """Print the AST for the given input file."""
        for input_file in self.input_files:
            ArxIO.file_to_buffer(input_file)
            lex = Lexer()
            tokens = lex.run()
            for token in tokens:
                print(token)

    def show_llvm_ir(self) -> None:
        """Compile into LLVM IR the given input file."""
        self.compile(show_llvm_ir=True)

    def run_shell(self) -> None:
        """Open arx in shell mode."""
        raise Exception("Arx Shell is not implemented yet.")

    def compile(self, show_llvm_ir: bool = False) -> None:
        """Compile the given input file."""
        for input_file in self.input_files:
            ArxIO.file_to_buffer(input_file)
            ast = Parser.parse()
            obj_gen = ObjectGenerator(
                input_file, self.output_file, self.is_lib
            )
            obj_gen.evaluate(ast, show_llvm_ir)
