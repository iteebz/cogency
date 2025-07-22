"""Test Time tool business logic."""

import pytest

from cogency.tools.time import Time


@pytest.mark.asyncio
async def test_time_interface():
    """Test time tool interface."""
    time_tool = Time()
    assert time_tool.name == "time"
    assert time_tool.description
    assert hasattr(time_tool, "run")


@pytest.mark.asyncio
async def test_current_time():
    """Test getting current time."""
    time_tool = Time()
    result = await time_tool.run(operation="now", timezone="UTC")
    assert "datetime" in result
    assert "timezone" in result
    assert "weekday" in result


@pytest.mark.asyncio
async def test_timezone_operations():
    """Test timezone conversion."""
    time_tool = Time()

    result = await time_tool.run(
        operation="convert_timezone",
        datetime_str="2024-01-15T14:30:00",
        from_tz="UTC",
        to_tz="America/New_York",
    )
    assert "converted" in result
    assert "to_timezone" in result


@pytest.mark.asyncio
async def test_relative_time():
    """Test relative time calculations."""
    time_tool = Time()

    result = await time_tool.run(
        operation="relative",
        datetime_str="2024-01-15T14:30:00",
        reference="2024-01-15T15:30:00",
    )
    assert "relative" in result
    assert "seconds_diff" in result


@pytest.mark.asyncio
async def test_city_timezones():
    """Test city name timezone mapping."""
    time_tool = Time()

    result = await time_tool.run(operation="now", timezone="london")
    assert "datetime" in result
    assert result["timezone"] == "Europe/London"


@pytest.mark.asyncio
async def test_error_handling():
    """Test error handling."""
    time_tool = Time()

    result = await time_tool.execute(operation="invalid_op")
    assert "error" in result
