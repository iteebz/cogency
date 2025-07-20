"""Test Time tool business logic."""
import pytest
from datetime import datetime

from cogency.tools.time import Time


class TestTime:
    """Test Time tool business logic."""
    
    @pytest.mark.asyncio
    async def test_basic_interface(self):
        """Time tool implements required interface."""
        time_tool = Time()
        
        # Required attributes
        assert time_tool.name == "time"
        assert time_tool.description
        assert hasattr(time_tool, 'run')
        
        # Schema and examples
        schema = time_tool.get_schema()
        examples = time_tool.get_usage_examples()
        assert isinstance(schema, str) and len(schema) > 0
        assert isinstance(examples, list) and len(examples) > 0
    
    @pytest.mark.asyncio
    async def test_current_time_utc(self):
        """Time tool can get current time for UTC."""
        time_tool = Time()
        
        result = await time_tool.run(operation="now", timezone="UTC")
        assert "datetime" in result
        assert "timezone" in result
        assert "weekday" in result
        assert "is_weekend" in result
    
    @pytest.mark.asyncio
    async def test_timezone_conversion(self):
        """Time tool can convert timezones."""
        time_tool = Time()
        
        result = await time_tool.run(operation="now", timezone="America/New_York")
        assert "datetime" in result
        assert "timezone" in result
    
    @pytest.mark.asyncio
    async def test_convert_timezone(self):
        """Time tool can convert between timezones."""
        time_tool = Time()
        
        result = await time_tool.run(
            operation="convert_timezone",
            datetime_str="2024-01-15T14:30:00",
            from_tz="UTC",
            to_tz="America/New_York"
        )
        assert "converted" in result
        assert "from_timezone" in result
        assert "to_timezone" in result
    
    @pytest.mark.asyncio
    async def test_relative_time(self):
        """Time tool can generate relative time descriptions."""
        time_tool = Time()
        
        result = await time_tool.run(
            operation="relative",
            datetime_str="2024-01-15T14:30:00",
            reference="2024-01-15T15:30:00"
        )
        assert "relative" in result
        assert "seconds_diff" in result
    
    @pytest.mark.asyncio
    async def test_city_timezone_mapping(self):
        """Time tool can handle city names as timezones."""
        time_tool = Time()
        
        result = await time_tool.run(operation="now", timezone="london")
        assert "datetime" in result
        assert "timezone" in result
        assert result["timezone"] == "Europe/London"
    
    @pytest.mark.asyncio
    async def test_relative_time_no_reference(self):
        """Time tool can generate relative time from now."""
        time_tool = Time()
        
        result = await time_tool.run(
            operation="relative",
            datetime_str="2024-01-15T14:30:00"
        )
        assert "relative" in result
        assert "seconds_diff" in result
        assert "reference" in result
    
    @pytest.mark.asyncio
    async def test_current_time_with_format(self):
        """Time tool can format current time."""
        time_tool = Time()
        
        result = await time_tool.run(
            operation="now",
            timezone="UTC",
            format="%Y-%m-%d %H:%M"
        )
        assert "datetime" in result
        assert "formatted" in result
        assert "timezone" in result
    
    @pytest.mark.asyncio
    async def test_invalid_timezone(self):
        """Time tool handles invalid timezones."""
        time_tool = Time()
        
        # Use execute() to test error handling
        result = await time_tool.execute(operation="now", timezone="Invalid/Timezone")
        assert "error" in result
    
    @pytest.mark.asyncio
    async def test_invalid_operation(self):
        """Time tool handles invalid operations."""
        time_tool = Time()
        
        result = await time_tool.execute(operation="invalid_op")
        assert "error" in result