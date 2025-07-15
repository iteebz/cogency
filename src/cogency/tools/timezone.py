"""Timezone tool using worldtimeapi.org - NO API KEY NEEDED."""
import logging
from typing import Any, Dict, List

import httpx

from .base import BaseTool

logger = logging.getLogger(__name__)


class TimezoneTool(BaseTool):
    """Get current time for any timezone/city using worldtimeapi.org (no API key required)."""

    def __init__(self):
        super().__init__(
            name="timezone",
            description="Get current time and date for any city or timezone worldwide"
        )

    async def run(self, location: str) -> Dict[str, Any]:
        """Get current time for a location.
        
        Args:
            location: City name or timezone (e.g., "New York", "America/New_York", "Europe/London")
            
        Returns:
            Time data including local time, timezone, UTC offset
        """
        try:
            # If location looks like a city, try to map it to timezone
            city_to_tz = {
                "new york": "America/New_York",
                "london": "Europe/London", 
                "tokyo": "Asia/Tokyo",
                "paris": "Europe/Paris",
                "sydney": "Australia/Sydney",
                "los angeles": "America/Los_Angeles",
                "chicago": "America/Chicago",
                "berlin": "Europe/Berlin",
                "mumbai": "Asia/Kolkata",
                "beijing": "Asia/Shanghai"
            }
            
            location_lower = location.lower()
            if location_lower in city_to_tz:
                timezone = city_to_tz[location_lower]
                url = f"https://worldtimeapi.org/api/timezone/{timezone}"
            else:
                url = f"https://worldtimeapi.org/api/timezone/{location}"
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
                
                if response.status_code == 404:
                    return {"error": f"Timezone/city '{location}' not found. Try format like 'America/New_York' or major city names."}
                
                response.raise_for_status()
                data = response.json()
                
                return {
                    "location": location,
                    "timezone": data["timezone"],
                    "datetime": data["datetime"][:19],  # Remove microseconds
                    "utc_offset": data["utc_offset"],
                    "day_of_year": data["day_of_year"],
                    "week_number": data["week_number"]
                }
                
        except httpx.TimeoutException:
            return {"error": f"Time service timeout for {location}"}
        except httpx.HTTPError as e:
            logger.error(f"HTTP error for {location}: {e}")
            return {"error": f"Failed to get time for {location}: {str(e)}"}
        except (KeyError, IndexError) as e:
            return {"error": f"Invalid time data format for {location}"}
        except Exception as e:
            logger.error(f"Timezone tool error: {e}")
            return {"error": f"Time lookup failed for {location}"}

    def get_schema(self) -> str:
        """Return the tool call schema."""
        return "timezone(location='string')"

    def get_usage_examples(self) -> List[str]:
        """Return example usage patterns."""
        return [
            "timezone(location='New York')",
            "timezone(location='Europe/London')",
            "timezone(location='Tokyo')"
        ]