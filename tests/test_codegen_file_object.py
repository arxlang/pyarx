from pathlib import Path

import pytest

from arx.codegen import ObjectGenerator
from arx.io import ArxIO
from arx.lexer import Lexer, TokenList
from arx.parser import Parser

PROJECT_PATH = Path(__file__).parent.parent.resolve()


@pytest.mark.parametrize(
    "code",
    [
        "1 + 1",
        "1 + 2 * (3 - 2)",
        "if (1 < 2):\n" "    3\n" "else:\n" "    2\n",
        "fn add_one(a):\n" "    a + 1\n" "add_one(1)\n",
    ],
)
@pytest.mark.skip(reason="codegen with llvm is paused for now")
def test_object_generation(code: str) -> None:
    lexer = Lexer()
    lexer.clean()

    parser = Parser()
    parser.clean()

    tokens = TokenList([])

    ArxIO.string_to_buffer(code)
    ast = parser.parse(tokens)
    objgen = ObjectGenerator()
    objgen.evaluate(ast)
    # remove temporary object file generated
    (PROJECT_PATH / "tmp.o").unlink()
