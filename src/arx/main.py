"""Arx main module."""
from arx.io import ArxIO
from arx.parser import Parser
from arx.codegen.ast_output import ASTtoOutput
from arx.codegen.file_object import ObjectGenerator


class ArxMain:
    """The main class for calling Arx compiler."""

    input_file: str
    output_file: str
    is_lib: bool

    def run(self, *args, **kwargs):
        """Compile the given source code."""

        self.input_file = kwargs.get("input_file", "")
        self.output_file = kwargs.get("output_file", "")
        # is_lib now is the only available option
        self.is_lib = kwargs.get("is_lib", True) or True

        if kwargs.get("show_ast"):
            return self.show_ast()

        if kwargs.get("show_llvm_ir"):
            return self.show_llvm_ir()

        if kwargs.get("shell"):
            return self.run_shell()

        self.compile()

    def show_ast(self):
        ArxIO.file_to_buffer(self.input_file)
        ast = Parser.parse()
        printer = ASTtoOutput()
        printer.emit_ast(ast)

    def show_llvm_ir(self):
        self.compile(show_llvm_ir=True)

    def run_shell(self):
        raise Exception("Arx Shell is not implemented yet.")

    def compile(self, show_llvm_ir: bool = False):
        ArxIO.file_to_buffer(self.input_file)
        ast = Parser.parse()
        obj_gen = ObjectGenerator(
            self.input_file, self.output_file, self.is_lib
        )
        obj_gen.evaluate(ast, show_llvm_ir)
