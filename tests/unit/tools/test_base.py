"""Tool base tests."""

import pytest

from cogency.tools.calculator import Calculator


@pytest.mark.asyncio
async def test_interface():
    calc = Calculator()

    assert hasattr(calc, "name")
    assert hasattr(calc, "description")
    assert calc.name == "calculator"

    assert hasattr(calc, "run")
    assert hasattr(calc, "schema")
    assert hasattr(calc, "examples")

    schema = calc.schema
    examples = calc.examples

    assert isinstance(schema, str) and len(schema) > 0
    assert isinstance(examples, list) and len(examples) > 0


@pytest.mark.asyncio
async def test_error_handling():
    calc = Calculator()

    result = await calc.run(expression="invalid expression $")
    assert not result.success
    assert result.error is not None

    result = await calc.execute()
    assert not result.success
    assert result.error is not None


@pytest.mark.asyncio
async def test_execute_wrapper():
    calc = Calculator()

    result = await calc.execute(operation=None, x1="not_a_number")
    assert not result.success
    assert result.error is not None
