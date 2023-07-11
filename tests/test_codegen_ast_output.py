import pytest

from arx.ast import BlockAST
from arx.codegen.ast_output import ASTtoOutput
from arx.io import ArxIO
from arx.lexer import Lexer
from arx.parser import Parser


@pytest.mark.parametrize(
    "code",
    [
        "1 + 1",
        "1 + 2 * (3 - 2)",
        "if (1 < 2):\n" "    3\n" "else:\n" "    2\n",
        "fn add_one(a):\n" "    a + 1\n" "add_one(1)\n",
    ],
)
def test_ast_to_output(code: str) -> None:
    Lexer.clean()
    Parser.clean()
    ArxIO.string_to_buffer(code)

    ast = Parser.parse()
    printer = ASTtoOutput()
    printer.emit_ast(ast)
