import pytest

from arx.io import ArxIO
from arx.parser import Parser
from arx.codegen.ast_to_object import ObjectGenerator


@pytest.mark.parametrize(
    "code",
    [
        "1",
        "1 + 1",
        "1 + 2 * (3 - 2)",
        """
        if (1 < 2):
            3
        """,
        """
        fn add_one(a):
            a + 1
        add(1)
        """,
    ],
)
def test_objeject_generation(code):
    ArxIO.string_to_buffer(code)
    ast = Parser.parse()
    objgen = ObjectGenerator()
    objgen.evaluate(ast)
