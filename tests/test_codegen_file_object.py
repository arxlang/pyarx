from pathlib import Path

import pytest

from arx.io import ArxIO
from arx.parser import Parser
from arx.codegen.file_object import ObjectGenerator

PROJECT_PATH = Path(__file__).parent.parent.resolve()


@pytest.mark.parametrize(
    "code",
    [
        "1 + 1",
        "1 + 2 * (3 - 2)",
        """
        if (1 < 2):
            3
        else:
            2
        """,
        """
        fn add_one(a):
            a + 1
        add_one(1)
        """,
    ],
)
def test_objeject_generation(code):
    ArxIO.string_to_buffer(code)
    ast = Parser.parse()
    objgen = ObjectGenerator()
    objgen.evaluate(ast)
    # remove temporary object file generated
    (PROJECT_PATH / "tmp.o").unlink()
