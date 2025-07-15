"""Timezone tool unit tests."""
import pytest
from cogency.tools.timezone import TimezoneTool


class TestTimezoneTool:
    """Test timezone tool functionality."""
    
    @pytest.mark.asyncio
    async def test_get_time(self):
        """Test getting current time."""
        tz = TimezoneTool()
        result = await tz.run("get_time", "UTC")
        
        assert "time" in result
        assert "timezone" in result
        assert result["timezone"] == "UTC"
    
    @pytest.mark.asyncio
    async def test_convert_time(self):
        """Test converting time between timezones."""
        tz = TimezoneTool()
        result = await tz.run("convert", "12:00", "UTC", "America/New_York")
        
        assert "converted_time" in result
        assert "from_timezone" in result
        assert "to_timezone" in result
        assert result["from_timezone"] == "UTC"
        assert result["to_timezone"] == "America/New_York"
    
    @pytest.mark.asyncio
    async def test_invalid_action(self):
        """Test invalid action handling."""
        tz = TimezoneTool()
        with pytest.raises(ValueError):
            await tz.run("invalid_action", "timezone")