from pathlib import Path

import pytest

from arx.io import ArxIO
from arx.lexer import Lexer
from arx.parser import Parser
from arx.codegen.file_object import ObjectGenerator

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
    Lexer.clean()
    Parser.clean()
    ArxIO.string_to_buffer(code)
    ast = Parser.parse()
    objgen = ObjectGenerator()
    objgen.evaluate(ast)
    # remove temporary object file generated
    (PROJECT_PATH / "tmp.o").unlink()
