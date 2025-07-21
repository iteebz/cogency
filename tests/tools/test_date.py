"""Test Date tool business logic."""

import pytest

from cogency.tools.date import Date


@pytest.fixture
def date_tool():
    return Date()


@pytest.mark.asyncio
async def test_date_operations(date_tool):
    """Test core date operations."""
    # Parse date
    result = await date_tool.run(operation="parse", date_string="2024-01-15")
    assert "parsed" in result
    assert "weekday" in result
    assert "is_weekend" in result

    # Format date
    result = await date_tool.run(operation="format", date_str="2024-01-15", format="%B %d, %Y")
    assert "formatted" in result
    assert "original" in result

    # Date arithmetic
    result = await date_tool.run(operation="add", date_str="2024-01-15", days=7)
    assert "result" in result
    assert "added" in result

    # Date difference
    result = await date_tool.run(operation="diff", start_date="2024-01-15", end_date="2024-01-20")
    assert "days" in result
    assert result["days"] == 5


@pytest.mark.asyncio
async def test_date_errors(date_tool):
    """Test error handling."""
    # Invalid operation
    result = await date_tool.execute(operation="invalid_op")
    assert "error" in result


@pytest.mark.asyncio
async def test_date_schema(date_tool):
    """Test schema validation."""
    schema = date_tool.schema()
    examples = date_tool.examples()

    assert isinstance(schema, str)
    assert isinstance(examples, list)
    assert len(examples) > 0
