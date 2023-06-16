from arx.ast import TreeAST
from arx.codegen.ast_to_output import emit_ast
from arx.io import ArxIO
from arx.parser import Parser


def test_ast_to_output():
    ArxIO.string_to_buffer(
        """
    fn add_one(a):
      a + 1

    add(1);
    """
    )

    ast = Parser.parse()
    emit_ast(ast)
