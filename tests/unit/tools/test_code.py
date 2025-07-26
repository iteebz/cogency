"""Test Code tool business logic."""

import pytest

from cogency.tools.code import Code


@pytest.mark.asyncio
async def test_basic_interface():
    code = Code()

    assert code.name == "code"
    assert code.description
    assert hasattr(code, "run")

    schema = code.schema
    examples = code.examples
    assert isinstance(schema, str) and len(schema) > 0
    assert isinstance(examples, list) and len(examples) > 0


@pytest.mark.asyncio
async def test_python_exec():
    code = Code()

    result = await code.run(code="print(2 + 2)", language="python")
    assert result.success
    assert result.data["exit_code"] == 0
    assert result.data["output"]
