"""Weather tool using Open-Meteo - NO API KEY NEEDED."""
import logging
from typing import Any, Dict, List

import httpx

from .base import BaseTool
from .registry import tool
# Error handling now in BaseTool.execute() - no decorators needed

logger = logging.getLogger(__name__)


@tool
class Weather(BaseTool):
    """Get current weather for any city using Open-Meteo (no API key required)."""

    def __init__(self):
        super().__init__(
            name="weather",
            description="Get current weather conditions for any city worldwide"
        )

    async def _geocode_city(self, city: str) -> Dict[str, Any]:
        """Get coordinates for a city using Open-Meteo geocoding."""
        url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1&language=en&format=json"
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()
            
            if not data.get("results"):
                raise ValueError(f"City '{city}' not found")
                
            result = data["results"][0]
            return {
                "latitude": result["latitude"],
                "longitude": result["longitude"],
                "name": result["name"],
                "country": result.get("country", "")
            }


    async def run(self, city: str, **kwargs) -> Dict[str, Any]:
        """Get weather for a city.
        
        Args:
            city: City name (e.g., "San Francisco", "London", "Tokyo")
            
        Returns:
            Weather data including temperature, conditions, humidity
        """
        # Get coordinates for the city
        location = await self._geocode_city(city)
        
        # Get weather data
        url = (
            f"https://api.open-meteo.com/v1/forecast"
            f"?latitude={location['latitude']}&longitude={location['longitude']}"
            f"&current=temperature_2m,relative_humidity_2m,apparent_temperature,"
            f"weather_code,wind_speed_10m,wind_direction_10m"
            f"&timezone=auto"
        )
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            
            data = response.json()
            current = data["current"]
            
            # Convert weather code to description
            weather_descriptions = {
                0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
                45: "Fog", 48: "Depositing rime fog",
                51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
                56: "Light freezing drizzle", 57: "Dense freezing drizzle",
                61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
                66: "Light freezing rain", 67: "Heavy freezing rain",
                71: "Slight snow", 73: "Moderate snow", 75: "Heavy snow",
                77: "Snow grains", 80: "Slight rain showers", 81: "Moderate rain showers",
                82: "Violent rain showers", 85: "Slight snow showers", 86: "Heavy snow showers",
                95: "Thunderstorm", 96: "Thunderstorm with slight hail", 99: "Thunderstorm with heavy hail"
            }
            
            condition = weather_descriptions.get(current["weather_code"], "Unknown")
            temp_c = current["temperature_2m"]
            temp_f = round(temp_c * 9/5 + 32, 1)
            
            return {
                "city": f"{location['name']}, {location['country']}",
                "temperature": f"{temp_c}°C ({temp_f}°F)",
                "condition": condition,
                "humidity": f"{current['relative_humidity_2m']}%",
                "wind": f"{current['wind_speed_10m']} km/h",
                "feels_like": f"{current['apparent_temperature']}°C"
            }

    def get_schema(self) -> str:
        """Return the tool call schema."""
        return "weather(city='string')"

    def get_usage_examples(self) -> List[str]:
        """Return example usage patterns."""
        return [
            "weather(city='New York')",
            "weather(city='London')", 
            "weather(city='Tokyo')"
        ]