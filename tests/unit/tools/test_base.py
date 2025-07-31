"""Tool base tests."""

import pytest

from cogency.tools.code import Code


@pytest.mark.asyncio
async def test_interface():
    code_tool = Code()

    assert hasattr(code_tool, "name")
    assert hasattr(code_tool, "description")
    assert code_tool.name == "code"

    assert hasattr(code_tool, "run")
    assert hasattr(code_tool, "schema")
    assert hasattr(code_tool, "examples")

    schema = code_tool.schema
    examples = code_tool.examples

    assert isinstance(schema, str) and len(schema) > 0
    assert isinstance(examples, list) and len(examples) > 0
