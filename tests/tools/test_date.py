"""Test Date tool business logic."""
import pytest
from datetime import datetime

from cogency.tools.date import Date


class TestDate:
    """Test Date tool business logic."""
    
    @pytest.mark.asyncio
    async def test_basic_interface(self):
        """Date tool implements required interface."""
        date_tool = Date()
        
        # Required attributes
        assert date_tool.name == "date"
        assert date_tool.description
        assert hasattr(date_tool, 'run')
        
        # Schema and examples
        schema = date_tool.schema()
        examples = date_tool.examples()
        assert isinstance(schema, str) and len(schema) > 0
        assert isinstance(examples, list) and len(examples) > 0
    
    @pytest.mark.asyncio
    async def test_parse_date(self):
        """Date tool can parse date strings."""
        date_tool = Date()
        
        result = await date_tool.run(operation="parse", date_string="2024-01-15")
        assert "parsed" in result
        assert "weekday" in result
        assert "is_weekend" in result
        assert "day_of_year" in result
        assert "week_number" in result
    
    @pytest.mark.asyncio
    async def test_format_date(self):
        """Date tool can format dates."""
        date_tool = Date()
        
        result = await date_tool.run(
            operation="format", 
            date_str="2024-01-15", 
            format="%B %d, %Y"
        )
        assert "formatted" in result
        assert "original" in result
        assert "format" in result
    
    @pytest.mark.asyncio
    async def test_date_arithmetic(self):
        """Date tool can add/subtract days and weeks."""
        date_tool = Date()
        
        # Test addition
        result = await date_tool.run(
            operation="add", 
            date_str="2024-01-15", 
            days=7
        )
        assert "result" in result
        assert "added" in result
        assert "weekday" in result
        assert "is_weekend" in result
        
        # Test subtraction
        result = await date_tool.run(
            operation="subtract", 
            date_str="2024-01-15", 
            weeks=1
        )
        assert "result" in result
        assert "subtracted" in result
    
    @pytest.mark.asyncio
    async def test_date_difference(self):
        """Date tool can calculate date differences."""
        date_tool = Date()
        
        result = await date_tool.run(
            operation="diff",
            start_date="2024-01-15",
            end_date="2024-01-20"
        )
        assert "days" in result
        assert "weeks" in result
        assert "human_readable" in result
        assert result["days"] == 5
    
    @pytest.mark.asyncio
    async def test_weekend_detection(self):
        """Date tool can detect weekends."""
        date_tool = Date()
        
        # Test a known weekend date (Saturday)
        result = await date_tool.run(
            operation="is_weekend",
            date_str="2024-01-13"  # Saturday
        )
        assert "is_weekend" in result
        assert "weekday" in result
        assert "weekday_number" in result
        assert result["is_weekend"] == True
    
    @pytest.mark.asyncio
    async def test_weekday_info(self):
        """Date tool can get weekday information."""
        date_tool = Date()
        
        result = await date_tool.run(
            operation="weekday",
            date_str="2024-01-15"  # Monday
        )
        assert "weekday" in result
        assert "weekday_short" in result
        assert "weekday_number" in result
        assert "is_weekend" in result
        assert result["weekday"] == "Monday"
        assert result["is_weekend"] == False
    
    @pytest.mark.asyncio
    async def test_invalid_operation(self):
        """Date tool handles invalid operations."""
        date_tool = Date()
        
        result = await date_tool.execute(operation="invalid_op")
        assert "error" in result
    
    @pytest.mark.asyncio
    async def test_missing_parameters(self):
        """Date tool handles missing required parameters."""
        date_tool = Date()
        
        # Test add without time units
        result = await date_tool.execute(operation="add", date_str="2024-01-15")
        assert "error" in result