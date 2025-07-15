"""Weather tool unit tests."""
import pytest
from unittest.mock import AsyncMock, Mock, patch
import httpx
from cogency.tools.weather import WeatherTool


class TestWeatherTool:
    """Test weather tool functionality."""
    
    @pytest.mark.asyncio
    async def test_get_weather(self):
        """Test getting weather with mock response."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "current_condition": [{
                "temp_C": "20",
                "temp_F": "68",
                "weatherDesc": [{"value": "Clear"}],
                "humidity": "60",
                "windspeedKmph": "10",
                "FeelsLikeC": "20"
            }]
        }
        # Mock the async get method to return the mock_response
        mock_client_get = AsyncMock(return_value=mock_response)

        # Mock the AsyncClient context manager
        mock_async_client = AsyncMock()
        mock_async_client.__aenter__.return_value.get = mock_client_get

        with patch('httpx.AsyncClient', return_value=mock_async_client):
            weather = WeatherTool()
            result = await weather.run("London")

            assert "city" in result
            assert "temperature" in result
            assert "condition" in result
            assert "humidity" in result
            assert "wind" in result
            assert "feels_like" in result
            mock_client_get.assert_called_once_with("http://wttr.in/London?format=j1")
    
    @pytest.mark.asyncio
    async def test_invalid_action(self):
        """Test invalid action handling."""
        weather = WeatherTool()
        result = await weather.run("invalid_action")
        assert "error" in result
        assert "Failed to get weather for invalid_action" in result["error"]