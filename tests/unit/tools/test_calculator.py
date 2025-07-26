"""Calculator tests."""

import pytest

from cogency.tools.calculator import Calculator


@pytest.mark.asyncio
async def test_basic_operations():
    calc = Calculator()

    result = await calc.run(expression="2 + 2")
    assert result.data["result"] == 4

    result = await calc.run(expression="10 - 3")
    assert result.data["result"] == 7

    result = await calc.run(expression="7 * 8")
    assert result.data["result"] == 56

    result = await calc.run(expression="10 / 2")
    assert result.data["result"] == 5

    result = await calc.run(expression="(15 + 27) * 2")
    assert result.data["result"] == 84


@pytest.mark.asyncio
async def test_errors():
    calc = Calculator()

    result = await calc.run(expression="4/0")
    assert not result.success
    assert "Cannot divide by zero" in result.error


@pytest.mark.asyncio
async def test_params():
    calc = Calculator()

    params = calc.params
    examples = calc.examples

    assert params is not None
    assert hasattr(params, "__annotations__")
    assert "expression" in params.__annotations__
    assert isinstance(examples, list)
    assert len(examples) > 0
