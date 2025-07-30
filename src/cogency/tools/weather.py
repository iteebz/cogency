"""Weather tool using Open-Meteo - NO API KEY NEEDED."""

import logging
from dataclasses import dataclass

import httpx
from resilient_result import Result

from cogency.tools.base import Tool
from cogency.tools.registry import tool

logger = logging.getLogger(__name__)


@dataclass
class WeatherArgs:
    city: str


@tool
class Weather(Tool):
    """Get current weather for any city using Open-Meteo (no API key required)."""

    # Clean weather formatting
    human_template = "{temperature}, {condition}"
    agent_template = "Weather in {city}: {temperature}, {condition}"
    param_key = "city"

    def __init__(self):
        super().__init__(
            name="weather",
            description="Get current weather conditions for any city worldwide",
            schema={
                "type": "object",
                "properties": {"city": {"type": "string", "description": "The name of the city"}},
                "required": ["city"],
            },
            emoji="🌤️",
            params=WeatherArgs,
            examples=[
                "weather(city='New York')",
                "weather(city='London')",
                "weather(city='Tokyo')",
            ],
            rules=[
                "Provide a specific, recognizable city name.",
            ],
        )

    async def _geocode_city(self, city: str) -> Result:
        """Get coordinates for a city using Open-Meteo geocoding."""
        # Schema validation handles required params

        url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1&language=en&format=json"
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                data = response.json()

                if not data.get("results"):
                    return Result.fail(f"City '{city}' not found")

                result = data["results"][0]
                return Result(
                    {
                        "latitude": result["latitude"],
                        "longitude": result["longitude"],
                        "name": result["name"],
                        "country": result.get("country", ""),
                    }
                )
        except httpx.RequestError as e:
            logger.error(f"Geocoding API request failed for {city}: {e}")
            return Result.fail(f"Failed to connect to geocoding service: {e}")
        except httpx.HTTPStatusError as e:
            logger.error(f"Geocoding API returned an error for {city}: {e}")
            return Result.fail(f"Geocoding API error: {e}")
        except Exception as e:
            logger.error(f"Unexpected error during geocoding for {city}: {e}")
            return Result.fail(f"Geocoding failed: {e}")

    async def run(self, city: str, **kwargs) -> Result:
        """Get weather for a city.

        Args:
            city: City name (e.g., "San Francisco", "London", "Tokyo")

        Returns:
            Weather data including temperature, conditions, humidity
        """
        try:
            # Get coordinates for the city
            location_result = await self._geocode_city(city)
            if not location_result.success:
                return location_result
            location = location_result.data

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
                    0: "Clear sky",
                    1: "Mainly clear",
                    2: "Partly cloudy",
                    3: "Overcast",
                    45: "Fog",
                    48: "Depositing rime fog",
                    51: "Light drizzle",
                    53: "Moderate drizzle",
                    55: "Dense drizzle",
                    56: "Light freezing drizzle",
                    57: "Dense freezing drizzle",
                    61: "Slight rain",
                    63: "Moderate rain",
                    65: "Heavy rain",
                    66: "Light freezing rain",
                    67: "Heavy freezing rain",
                    71: "Slight snow",
                    73: "Moderate snow",
                    75: "Heavy snow",
                    77: "Snow grains",
                    80: "Slight rain showers",
                    81: "Moderate rain showers",
                    82: "Violent rain showers",
                    85: "Slight snow showers",
                    86: "Heavy snow showers",
                    95: "Thunderstorm",
                    96: "Thunderstorm with slight hail",
                    99: "Thunderstorm with heavy hail",
                }

                condition = weather_descriptions.get(current["weather_code"], "Unknown")
                temp_c = current["temperature_2m"]
                temp_f = round(temp_c * 9 / 5 + 32, 1)

                return Result(
                    {
                        "city": f"{location['name']}, {location.get('country', '')}",
                        "temperature": f"{temp_c}°C ({temp_f}°F)",
                        "condition": condition,
                        "humidity": f"{current['relative_humidity_2m']}%",
                        "wind": f"{current['wind_speed_10m']} km/h",
                        "feels_like": f"{current['apparent_temperature']}°C",
                    }
                )
        except httpx.RequestError as e:
            logger.error(f"Weather API request failed for {city}: {e}")
            return Result.fail(f"Failed to connect to weather service: {e}")
        except httpx.HTTPStatusError as e:
            logger.error(f"Weather API returned an error for {city}: {e}")
            return Result.fail(f"Weather API error: {e}")
        except Exception as e:
            logger.error(f"Unexpected error during weather retrieval for {city}: {e}")
            return Result.fail(f"Weather retrieval failed: {e}")
