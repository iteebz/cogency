"""Time tool - focused time and timezone operations with zero network dependencies."""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional

import pytz
from dateutil import parser as date_parser
from resilient_result import Result

from cogency.tools.base import Tool
from cogency.tools.registry import tool

logger = logging.getLogger(__name__)


@dataclass
class TimeParams:
    operation: str
    timezone: Optional[str] = None
    datetime_str: Optional[str] = None
    from_tz: Optional[str] = None
    to_tz: Optional[str] = None


@tool
class Time(Tool):
    """Time operations: current time, timezone conversion, relative time."""

    def __init__(self):
        super().__init__(
            name="time",
            description="Time operations: current time, timezone conversion, relative time",
            schema="time(operation=str, timezone=str, datetime_str=str, from_tz=str, to_tz=str)",
            emoji="⏰",
            params=TimeParams,
            examples=[
                "time(operation='now')",
                "time(operation='now', timezone='Europe/London')",
                "time(operation='relative', datetime_str='2024-01-15T14:30:00')",
                "time(operation='convert_timezone', datetime_str='2024-01-15T14:30:00', from_tz='UTC', to_tz='America/New_York')",
            ],
            rules=[
                "Use city names (London, Tokyo) or IANA timezones",
            ],
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
            "vancouver": "America/Vancouver",
        }

    async def run(self, operation: str = "now", **kwargs) -> Result:
        """Execute time operation.

        Args:
            operation: Operation to perform (now, relative, convert_timezone)
            **kwargs: Operation-specific parameters

        Returns:
            Operation result with time data
        """
        if operation not in self._operations:
            return Result.fail(
                f"Unknown operation: {operation}. Available: {list(self._operations.keys())}"
            )

        return await self._operations[operation](**kwargs)

    async def _now(self, timezone: str = "UTC", format: str = None) -> Result:
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
            return Result.fail(f"Unknown timezone: {timezone_name}")

        now = datetime.now(tz)

        result = {
            "timezone": timezone_name,
            "datetime": now.isoformat(),
            "formatted": now.strftime(format) if format else now.strftime("%Y-%m-%d %H:%M:%S %Z"),
            "utc_offset": now.strftime("%z"),
            "weekday": now.strftime("%A"),
            "is_weekend": now.weekday() >= 5,
            "day_of_year": now.timetuple().tm_yday,
            "week_number": int(now.strftime("%W")),
        }

        return Result.ok(result)

    async def _relative(self, datetime_str: str, reference: str = None) -> Result:
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

            return Result.ok(
                {
                    "datetime": datetime_str,
                    "reference": reference or "now",
                    "relative": relative,
                    "seconds_diff": total_seconds,
                }
            )
        except Exception as e:
            return Result.fail(f"Failed to calculate relative time: {str(e)}")

    async def _convert_timezone(self, datetime_str: str, from_tz: str, to_tz: str) -> Result:
        """Convert datetime between timezones."""
        try:
            dt = date_parser.parse(datetime_str)

            if dt.tzinfo is None:
                from_timezone = pytz.timezone(from_tz)
                dt = from_timezone.localize(dt)

            to_timezone = pytz.timezone(to_tz)
            converted = dt.astimezone(to_timezone)

            return Result.ok(
                {
                    "original": datetime_str,
                    "from_timezone": from_tz,
                    "to_timezone": to_tz,
                    "converted": converted.isoformat(),
                    "formatted": converted.strftime("%Y-%m-%d %H:%M:%S %Z"),
                }
            )
        except Exception as e:
            logger.error(
                f"Failed to convert timezone from {from_tz} to {to_tz} for {datetime_str}: {e}"
            )
            return Result.fail(f"Failed to convert timezone: {str(e)}")

    def format_human(
        self, params: dict[str, Any], results: Optional[Result] = None
    ) -> tuple[str, str]:
        """Format time execution for display."""

        operation = params.get("operation", "")
        if operation == "now":
            tz = params.get("timezone", "UTC")
            param_str = f"(now, {tz})"
        elif operation == "relative":
            dt = params.get("datetime_str", "")
            param_str = f"(relative, {dt[:16]})" if dt else "(relative)"
        elif operation == "convert_timezone":
            from_tz = params.get("from_tz", "")
            to_tz = params.get("to_tz", "")
            param_str = f"(convert, {from_tz}→{to_tz})" if from_tz and to_tz else "(convert)"
        else:
            param_str = f"({operation})" if operation else ""

        if results is None:
            return param_str, ""

        # Format results
        if not results.success:
            result_str = f"Error: {results.error}"
        else:
            data = results.data
            if operation == "now":
                time_str = data.get("formatted", "")
                result_str = f"Current: {time_str[:19]}" if time_str else "Current time retrieved"
            elif operation == "relative":
                relative = data.get("relative", "")
                result_str = f"Relative: {relative}" if relative else "Relative time calculated"
            elif operation == "convert_timezone":
                converted = data.get("formatted", "")
                result_str = f"Converted: {converted[:19]}" if converted else "Timezone converted"
            else:
                result_str = "Time operation completed"

        return param_str, result_str

    def format_agent(self, result_data: Dict[str, Any]) -> str:
        """Format time results for agent action history."""
        if not result_data:
            return "No result"

        operation = result_data.get("operation", "")
        formatters = {
            "now": lambda data: f"Current time: {data.get('formatted', '')}",
            "relative": lambda data: f"Relative time: {data.get('relative', '')}",
            "convert_timezone": lambda data: f"Converted time: {data.get('formatted', '')}",
        }
        return formatters.get(operation, lambda data: "Time operation completed")(result_data)
