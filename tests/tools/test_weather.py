"""Test Weather tool business logic."""

import pytest

from cogency.tools.weather import Weather


class TestWeather:
    """Test Weather tool business logic."""

    @pytest.mark.asyncio
    async def test_basic_interface(self):
        """Weather tool implements required interface."""
        weather_tool = Weather()

        # Required attributes
        assert weather_tool.name == "weather"
        assert weather_tool.description
        assert hasattr(weather_tool, "run")

        # Schema and examples
        schema = weather_tool.schema()
        examples = weather_tool.examples()
        assert isinstance(schema, str) and len(schema) > 0
        assert isinstance(examples, list) and len(examples) > 0

    @pytest.mark.asyncio
    async def test_empty_city(self):
        """Weather tool handles empty city."""
        weather_tool = Weather()

        result = await weather_tool.execute(city="")
        assert "error" in result

    @pytest.mark.asyncio
    async def test_invalid_city(self):
        """Weather tool handles invalid city."""
        weather_tool = Weather()

        # Use a clearly invalid location
        result = await weather_tool.execute(city="ThisIsNotARealLocationXYZ123")
        # Should return error dict when city not found
        assert isinstance(result, dict)
        assert "error" in result
