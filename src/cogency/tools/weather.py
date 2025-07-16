"""Weather tool using wttr.in - NO API KEY NEEDED."""
import logging
from typing import Any, Dict, List

import httpx

from .base import BaseTool
from .registry import tool

logger = logging.getLogger(__name__)


@tool
class WeatherTool(BaseTool):
    """Get current weather for any city using wttr.in (no API key required)."""

    def __init__(self):
        super().__init__(
            name="weather",
            description="Get current weather conditions for any city worldwide"
        )

    async def run(self, city: str) -> Dict[str, Any]:
        """Get weather for a city.
        
        Args:
            city: City name (e.g., "San Francisco", "London", "Tokyo")
            
        Returns:
            Weather data including temperature, conditions, humidity
        """
        try:
            url = f"http://wttr.in/{city}?format=j1"
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                
                data = response.json()
                current = data["current_condition"][0]
                
                return {
                    "city": city,
                    "temperature": f"{current['temp_C']}°C ({current['temp_F']}°F)",
                    "condition": current["weatherDesc"][0]["value"],
                    "humidity": f"{current['humidity']}%",
                    "wind": f"{current['windspeedKmph']} km/h",
                    "feels_like": f"{current['FeelsLikeC']}°C"
                }
                
        except httpx.TimeoutException:
            return {"error": f"Weather service timeout for {city}"}
        except httpx.HTTPError as e:
            return {"error": f"Failed to get weather for {city}: {str(e)}"}
        except (KeyError, IndexError) as e:
            return {"error": f"Invalid weather data format for {city}"}
        except Exception as e:
            logger.error(f"Weather tool error: {e}")
            return {"error": f"Weather lookup failed for {city}"}

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