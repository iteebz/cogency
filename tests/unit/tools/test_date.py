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
    assert result.success
    data = result.data
    assert "parsed" in data
    assert "weekday" in data
    assert "is_weekend" in data

    # Format date
    result = await date_tool.run(operation="format", date_str="2024-01-15", format="%B %d, %Y")
    assert result.success
    data = result.data
    assert "formatted" in data
    assert "original" in data

    # Date arithmetic
    result = await date_tool.run(operation="add", date_str="2024-01-15", days=7)
    assert result.success
    data = result.data
    assert "result" in data
    assert "added" in data

    # Date difference
    result = await date_tool.run(operation="diff", start_date="2024-01-15", end_date="2024-01-20")
    assert result.success
    data = result.data
    assert "days" in data
    assert data["days"] == 5


@pytest.mark.asyncio
async def test_schema(date_tool):
    """Test schema validation."""
    schema = date_tool.schema
    examples = date_tool.examples

    assert isinstance(schema, str)
    assert isinstance(examples, list)
    assert len(examples) > 0
