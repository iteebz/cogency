"""Tool base tests."""

import pytest

from cogency.tools.files import Files


@pytest.mark.asyncio
async def test_interface():
    tool = Files()

    assert hasattr(tool, "name")
    assert hasattr(tool, "description")
    assert tool.name == "files"

    assert hasattr(tool, "run")
    assert hasattr(tool, "schema")
    assert hasattr(tool, "examples")

    schema = tool.schema
    examples = tool.examples

    assert isinstance(schema, str) and len(schema) > 0
    assert isinstance(examples, list) and len(examples) > 0
