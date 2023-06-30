from arx.ast import BlockAST
from arx.codegen.ast_output import ASTtoOutput
from arx.io import ArxIO
from arx.parser import Parser


def test_ast_to_output():
    ArxIO.string_to_buffer(
        "fn add_one(a):\n" + "  a + 1\n" + "\n" + "add(1);\n"
    )

    ast = Parser.parse()
    printer = ASTtoOutput()
    printer.emit_ast(ast)
