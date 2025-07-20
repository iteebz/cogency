"""Timezone tool using pytz - ROCK SOLID, NO NETWORK BULLSHIT."""
import logging
from datetime import datetime
from typing import Any, Dict, List

import pytz

from .base import BaseTool
from .registry import tool
# Error handling now in BaseTool.execute() - no decorators needed

logger = logging.getLogger(__name__)


@tool
class Time(BaseTool):
    """Time operations: timezone lookup, time formatting, time conversion - reliable local computation."""

    def __init__(self):
        super().__init__(
            name="timezone",
            description="Time operations: get time for any timezone/city, format times, compare times"
        )

    async def run(self, location: str) -> Dict[str, Any]:
        """Get current time for a location.
        
        Args:
            location: City name or timezone (e.g., "New York", "America/New_York", "Europe/London")
            
        Returns:
            Time data including local time, timezone, UTC offset
        """
        # If location looks like a city, try to map it to timezone
        city_to_tz = {
            "new york": "America/New_York",
            "london": "Europe/London", 
            "tokyo": "Asia/Tokyo",
            "paris": "Europe/Paris",
            "sydney": "Australia/Sydney",
            "melbourne": "Australia/Melbourne",
            "los angeles": "America/Los_Angeles",
            "san francisco": "America/Los_Angeles",
            "chicago": "America/Chicago",
            "berlin": "Europe/Berlin",
            "mumbai": "Asia/Kolkata",
            "beijing": "Asia/Shanghai"
        }
        
        location_lower = location.lower()
        if location_lower in city_to_tz:
            timezone_name = city_to_tz[location_lower]
        else:
            timezone_name = location
        
        # Get timezone object
        tz = pytz.timezone(timezone_name)
        now = datetime.now(tz)
        
        # Format like the old API response for consistency
        return {
            "location": location,
            "timezone": timezone_name,
            "datetime": now.strftime("%Y-%m-%d %H:%M:%S"),
            "utc_offset": now.strftime("%z"),
            "day_of_year": now.timetuple().tm_yday,
            "week_number": int(now.strftime("%W"))
        }

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