"""Weather tool unit tests."""
import pytest
from unittest.mock import AsyncMock, patch
from cogency.tools.weather import WeatherTool


class TestWeatherTool:
    """Test weather tool functionality."""
    
    @pytest.mark.asyncio
    async def test_get_weather(self):
        """Test getting weather with mock response."""
        with patch('aiohttp.ClientSession.get') as mock_get:
            # Mock the response
            mock_response = AsyncMock()
            mock_response.json = AsyncMock(return_value={
                "name": "New York",
                "main": {"temp": 22.5, "humidity": 60},
                "weather": [{"description": "clear sky"}]
            })
            mock_get.return_value.__aenter__.return_value = mock_response
            
            weather = WeatherTool()
            result = await weather.run("get_weather", "New York")
            
            assert "location" in result
            assert "temperature" in result
            assert "description" in result
    
    @pytest.mark.asyncio
    async def test_invalid_action(self):
        """Test invalid action handling."""
        weather = WeatherTool()
        with pytest.raises(ValueError):
            await weather.run("invalid_action", "location")