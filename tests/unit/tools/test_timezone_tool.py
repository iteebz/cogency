"""Timezone tool unit tests."""
import pytest
from cogency.tools.timezone import TimezoneTool


class TestTimezoneTool:
    """Test the TimezoneTool."""

    @pytest.mark.asyncio
    async def test_get_time_valid_location(self):
        """Test getting current time for a valid location."""
        tz = TimezoneTool()
        result = await tz.run("America/New_York")
        assert "location" in result
        assert "timezone" in result
        assert "datetime" in result
        assert "utc_offset" in result
        assert result["location"] == "America/New_York"

    @pytest.mark.asyncio
    async def test_get_time_invalid_location(self):
        """Test getting current time for an invalid location."""
        tz = TimezoneTool()
        result = await tz.run("Invalid/Timezone")
        assert "error" in result
        assert "not found" in result["error"]