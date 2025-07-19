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
        # Mock geocoding response
        mock_geocode_response = Mock()
        mock_geocode_response.json.return_value = {
            "results": [{
                "latitude": 51.5074,
                "longitude": -0.1278,
                "name": "London",
                "country": "United Kingdom"
            }]
        }
        
        # Mock weather response
        mock_weather_response = Mock()
        mock_weather_response.json.return_value = {
            "current": {
                "temperature_2m": 20.0,
                "relative_humidity_2m": 60,
                "weather_code": 1,
                "wind_speed_10m": 10.0,
                "apparent_temperature": 20.0
            }
        }
        
        # Mock the async get method to return different responses
        mock_client_get = AsyncMock(side_effect=[mock_geocode_response, mock_weather_response])

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
            assert result["city"] == "London, United Kingdom"
            assert result["temperature"] == "20.0°C (68.0°F)"
            assert result["condition"] == "Mainly clear"
            assert result["humidity"] == "60%"
            assert result["wind"] == "10.0 km/h"
            assert result["feels_like"] == "20.0°C"
    
    @pytest.mark.asyncio
    async def test_city_not_found(self):
        """Test handling when city is not found."""
        mock_geocode_response = Mock()
        mock_geocode_response.json.return_value = {"results": []}
        mock_client_get = AsyncMock(return_value=mock_geocode_response)
        mock_async_client = AsyncMock()
        mock_async_client.__aenter__.return_value.get = mock_client_get

        with patch('httpx.AsyncClient', return_value=mock_async_client):
            weather = WeatherTool()
            result = await weather.run("NonexistentCity")
            assert "error" in result
            assert "not found" in result["error"]
    
    @pytest.mark.asyncio
    async def test_http_error(self):
        """Test HTTP error handling."""
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Bad Request", request=httpx.Request("GET", "http://example.com"), response=httpx.Response(400)
        )

        mock_client_get = AsyncMock(return_value=mock_response)
        mock_async_client = AsyncMock()
        mock_async_client.__aenter__.return_value.get = mock_client_get

        with patch('httpx.AsyncClient', return_value=mock_async_client):
            weather = WeatherTool()
            result = await weather.run("TestCity")
            assert "error" in result
            assert "Failed to get weather for TestCity" in result["error"]