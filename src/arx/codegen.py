"""File Object, Executable or LLVM IR generation."""

import logging

import astx

from irx.builders.llvmliteir import LLVMLiteIR

from arx.io import ArxIO
from arx.lexer import Lexer
from arx.parser import Parser

logging.basicConfig(level=logging.INFO)
LOG = logging.getLogger(__name__)


INPUT_FILE: str = ""
OUTPUT_FILE: str = ""
ARX_VERSION: str = ""
IS_BUILD_LIB: bool = True


class ObjectGenerator:
    """Generate object files or executable from an AST."""

    output_file: str = ""
    input_file: str = ""
    # is_lib: bool = True

    def __init__(
        self,
        input_file: str = "",
        output_file: str = "tmp.o",
        is_lib: bool = True,
    ):
        self.input_file = input_file
        self.output_file = output_file or f"{input_file}.o"
        self.is_lib = is_lib

    def evaluate(self, ast_node: astx.AST, show_llvm_ir: bool = False) -> None:
        """
        Compile an AST to an object file.

        Parameters
        ----------
            ast_node: An AST object.

        Returns
        -------
            int: The compilation result.
        """
        logging.info("Starting main_loop")

        builder = LLVMLiteIR()

        # Convert LLVM IR into in-memory representation
        if show_llvm_ir:
            return print(str(builder.translate(ast_node)))

        builder.build(ast_node, self.output_file)

    def open_interactive(self) -> None:
        """
        Open the Arx shell.

        Returns
        -------
            int: The compilation result.
        """
        # Prime the first token.
        print(f"Arx {ARX_VERSION} \n")
        print(">>> ")

        lexer = Lexer()
        parser = Parser()

        while True:
            try:
                ArxIO.string_to_buffer(input())
                self.evaluate(parser.parse(lexer.lex()))
            except KeyboardInterrupt:
                break
