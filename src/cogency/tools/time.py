"""Time tool - focused time and timezone operations with zero network dependencies."""
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union

import pytz
from dateutil import parser as date_parser

from .base import BaseTool
from .registry import tool
from cogency.errors import ValidationError, ToolError

logger = logging.getLogger(__name__)


@tool
class Time(BaseTool):
    """Time operations: current time, timezone conversion, relative time."""

    def __init__(self):
        super().__init__(
            name="time",
            description="Time operations: current time, timezone conversion, relative time",
            emoji="⏰"
        )
        
        self._operations = {
            "now": self._now,
            "relative": self._relative,
            "convert_timezone": self._convert_timezone,
        }
        
        self._city_to_tz = {
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
            "beijing": "Asia/Shanghai",
            "dubai": "Asia/Dubai",
            "moscow": "Europe/Moscow",
            "toronto": "America/Toronto",
            "vancouver": "America/Vancouver"
        }

    async def run(self, operation: str = "now", **kwargs) -> Dict[str, Any]:
        """Execute time operation.
        
        Args:
            operation: Operation to perform (now, relative, convert_timezone)
            **kwargs: Operation-specific parameters
            
        Returns:
            Operation result with time data
        """
        if operation not in self._operations:
            raise ValidationError(
                f"Unknown operation: {operation}. Available: {list(self._operations.keys())}"
            )
        
        return await self._operations[operation](**kwargs)
    
    async def _now(self, timezone: str = "UTC", format: str = None) -> Dict[str, Any]:
        """Get current time for timezone."""
        # Handle both location names and timezone names
        location_lower = timezone.lower()
        if location_lower in self._city_to_tz:
            timezone_name = self._city_to_tz[location_lower]
        else:
            timezone_name = timezone
        
        try:
            tz = pytz.timezone(timezone_name)
        except pytz.UnknownTimeZoneError:
            raise ToolError(f"Unknown timezone: {timezone_name}")
        
        now = datetime.now(tz)
        
        result = {
            "timezone": timezone_name,
            "datetime": now.isoformat(),
            "formatted": now.strftime(format) if format else now.strftime("%Y-%m-%d %H:%M:%S %Z"),
            "utc_offset": now.strftime("%z"),
            "weekday": now.strftime("%A"),
            "is_weekend": now.weekday() >= 5,
            "day_of_year": now.timetuple().tm_yday,
            "week_number": int(now.strftime("%W"))
        }
        
        return result
    
    async def _relative(self, datetime_str: str, reference: str = None) -> Dict[str, Any]:
        """Get relative time description."""
        try:
            dt = date_parser.parse(datetime_str)
            
            if reference:
                ref_dt = date_parser.parse(reference)
            else:
                if dt.tzinfo is None:
                    # If input is naive, assume UTC and make both naive
                    ref_dt = datetime.now()
                else:
                    # If input has timezone, use that timezone for reference
                    ref_dt = datetime.now(dt.tzinfo)
            
            diff = dt - ref_dt
            total_seconds = diff.total_seconds()
            
            if abs(total_seconds) < 60:
                relative = "just now"
            elif abs(total_seconds) < 3600:
                minutes = int(abs(total_seconds) // 60)
                relative = f"{minutes} minute{'s' if minutes != 1 else ''} {'ago' if total_seconds < 0 else 'from now'}"
            elif abs(total_seconds) < 86400:
                hours = int(abs(total_seconds) // 3600)
                relative = f"{hours} hour{'s' if hours != 1 else ''} {'ago' if total_seconds < 0 else 'from now'}"
            else:
                days = int(abs(total_seconds) // 86400)
                relative = f"{days} day{'s' if days != 1 else ''} {'ago' if total_seconds < 0 else 'from now'}"
            
            return {
                "datetime": datetime_str,
                "reference": reference or "now",
                "relative": relative,
                "seconds_diff": total_seconds
            }
        except Exception as e:
            raise ToolError(f"Failed to calculate relative time: {str(e)}")
    
    async def _convert_timezone(self, datetime_str: str, from_tz: str, to_tz: str) -> Dict[str, Any]:
        """Convert datetime between timezones."""
        try:
            dt = date_parser.parse(datetime_str)
            
            if dt.tzinfo is None:
                from_timezone = pytz.timezone(from_tz)
                dt = from_timezone.localize(dt)
            
            to_timezone = pytz.timezone(to_tz)
            converted = dt.astimezone(to_timezone)
            
            return {
                "original": datetime_str,
                "from_timezone": from_tz,
                "to_timezone": to_tz,
                "converted": converted.isoformat(),
                "formatted": converted.strftime("%Y-%m-%d %H:%M:%S %Z")
            }
        except Exception as e:
            raise ToolError(f"Failed to convert timezone: {str(e)}")

    def get_schema(self) -> str:
        return "time(operation='now|relative|convert_timezone', timezone='UTC|London|Tokyo|...', datetime_str='...', from_tz='...', to_tz='...')"

    def get_usage_examples(self) -> List[str]:
        return [
            "time(operation='now', timezone='Europe/London')",
            "time(operation='relative', datetime_str='2024-01-15T14:30:00')",
            "time(operation='convert_timezone', datetime_str='2024-01-15T14:30:00', from_tz='UTC', to_tz='America/New_York')"
        ]