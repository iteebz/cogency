"""Date tool - focused date operations with zero network dependencies."""

import logging
from dataclasses import dataclass
from datetime import timedelta
from typing import Any, Dict, Optional

import pytz
from dateutil import parser as date_parser
from resilient_result import Result

from cogency.tools.base import Tool
from cogency.tools.registry import tool

logger = logging.getLogger(__name__)


@dataclass
class DateArgs:
    operation: str
    date_str: Optional[str] = None
    format: Optional[str] = None
    days: Optional[int] = None
    weeks: Optional[int] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None


@tool
class Date(Tool):
    """Date operations: parsing, formatting, arithmetic, weekday calculations."""

    def __init__(self):
        super().__init__(
            name="date",
            description="Date operations: parsing, formatting, arithmetic, weekday calculations",
            schema="date(operation=str, date_str=str, format=str, days=int, weeks=int, start_date=str, end_date=str)",
            emoji="📅",
            params=DateArgs,
            examples=[
                "date(operation='parse', date_str='2024-01-15')",
                "date(operation='add', date_str='2024-01-15', days=7)",
                "date(operation='format', date_str='2024-01-15', format='%B %d, %Y')",
                "date(operation='diff', start_date='2024-01-01', end_date='2024-01-15')",
            ],
            rules=[
                "Date strings are auto-parsed",
            ],
        )
        self._operations = {
            "parse": self._parse,
            "format": self._format,
            "add": self._add,
            "subtract": self._subtract,
            "diff": self._diff,
            "is_weekend": self._is_weekend,
            "weekday": self._weekday,
        }

    async def run(self, operation: str = "parse", **kwargs) -> Result:
        """Execute date operation.
        Args:
            operation: Operation to perform (parse, format, add, subtract, diff, is_weekend, weekday)
            **kwargs: Operation-specific parameters
        Returns:
            Operation result with date data
        """
        if operation not in self._operations:
            return Result.fail(
                f"Unknown operation: {operation}. Available: {list(self._operations.keys())}"
            )
        return await self._operations[operation](**kwargs)

    async def _parse(self, date_string: str, timezone: str = None) -> Result:
        """Parse date string."""
        try:
            parsed = date_parser.parse(date_string)
            if timezone:
                if parsed.tzinfo is None:
                    tz = pytz.timezone(timezone)
                    parsed = tz.localize(parsed)
                else:
                    tz = pytz.timezone(timezone)
                    parsed = parsed.astimezone(tz)
            return Result.ok(
                {
                    "original": date_string,
                    "parsed": parsed.date().isoformat(),
                    "weekday": parsed.strftime("%A"),
                    "is_weekend": parsed.weekday() >= 5,
                    "day_of_year": parsed.timetuple().tm_yday,
                    "week_number": int(parsed.strftime("%W")),
                }
            )
        except Exception as e:
            return Result.fail(f"Failed to parse date string '{date_string}': {str(e)}")

    async def _format(self, date_str: str, format: str) -> Result:
        """Format date string."""
        try:
            dt = date_parser.parse(date_str)
            formatted = dt.strftime(format)
            return Result.ok({"original": date_str, "format": format, "formatted": formatted})
        except Exception as e:
            return Result.fail(f"Failed to format date: {str(e)}")

    async def _add(self, date_str: str, **kwargs) -> Result:
        """Add time to date."""
        try:
            dt = date_parser.parse(date_str)
            delta_kwargs = {}
            for key in ["days", "weeks"]:
                if key in kwargs:
                    delta_kwargs[key] = kwargs[key]
            if not delta_kwargs:
                return Result.fail("No time units provided. Use days or weeks.")
            delta = timedelta(**delta_kwargs)
            result_dt = dt + delta
            return Result.ok(
                {
                    "original": date_str,
                    "added": delta_kwargs,
                    "result": result_dt.date().isoformat(),
                    "weekday": result_dt.strftime("%A"),
                    "is_weekend": result_dt.weekday() >= 5,
                }
            )
        except Exception as e:
            return Result.fail(f"Failed to add time: {str(e)}")

    async def _subtract(self, date_str: str, **kwargs) -> Result:
        """Subtract time from date."""
        try:
            dt = date_parser.parse(date_str)
            delta_kwargs = {}
            for key in ["days", "weeks"]:
                if key in kwargs:
                    delta_kwargs[key] = kwargs[key]
            if not delta_kwargs:
                return Result.fail("No time units provided. Use days or weeks.")
            delta = timedelta(**delta_kwargs)
            result_dt = dt - delta
            return Result.ok(
                {
                    "original": date_str,
                    "subtracted": delta_kwargs,
                    "result": result_dt.date().isoformat(),
                    "weekday": result_dt.strftime("%A"),
                    "is_weekend": result_dt.weekday() >= 5,
                }
            )
        except Exception as e:
            return Result.fail(f"Failed to subtract time: {str(e)}")

    async def _diff(self, start_date: str, end_date: str) -> Result:
        """Calculate difference between two dates."""
        try:
            start = date_parser.parse(start_date)
            end = date_parser.parse(end_date)
            diff = end.date() - start.date()
            return Result.ok(
                {
                    "start": start_date,
                    "end": end_date,
                    "days": diff.days,
                    "weeks": diff.days // 7,
                    "human_readable": f"{diff.days} days",
                }
            )
        except Exception as e:
            return Result.fail(f"Failed to calculate difference: {str(e)}")

    async def _is_weekend(self, date_str: str) -> Result:
        """Check if date falls on weekend."""
        try:
            dt = date_parser.parse(date_str)
            is_weekend = dt.weekday() >= 5
            return Result.ok(
                {
                    "date": date_str,
                    "is_weekend": is_weekend,
                    "weekday": dt.strftime("%A"),
                    "weekday_number": dt.weekday(),
                }
            )
        except Exception as e:
            return Result.fail(f"Failed to check weekend: {str(e)}")

    async def _weekday(self, date_str: str) -> Result:
        """Get weekday information."""
        try:
            dt = date_parser.parse(date_str)
            return Result.ok(
                {
                    "date": date_str,
                    "weekday": dt.strftime("%A"),
                    "weekday_short": dt.strftime("%a"),
                    "weekday_number": dt.weekday(),
                    "is_weekend": dt.weekday() >= 5,
                }
            )
        except Exception as e:
            return Result.fail(f"Failed to get weekday: {str(e)}")

    def format_human(
        self, params: Dict[str, Any], results: Optional[Result] = None
    ) -> tuple[str, str]:
        """Format date execution for display."""
        operation = params.get("operation", "")
        if operation == "parse":
            date_string = params.get("date_string", "")
            param_str = f"(parse: {date_string[:10]})" if date_string else "(parse)"
        elif operation in ["add", "subtract"]:
            date_str = params.get("date_str", "")
            param_str = f"({operation}: {date_str[:10]})" if date_str else f"({operation})"
        elif operation == "diff":
            start = params.get("start_date", "")
            end = params.get("end_date", "")
            param_str = f"(diff: {start[:10]}-{end[:10]})" if start and end else "(diff)"
        else:
            param_str = f"({operation})"
        if results is None:
            return param_str, ""
        # Format results
        if not results.success:
            result_str = f"Error: {results.error}"
        else:
            data = results.data
            if data.get("parsed"):
                result_str = f"Parsed: {data['parsed']}"
            elif data.get("result"):
                result_str = f"Result: {data['result']}"
            elif data.get("days") is not None:
                result_str = f"{data['days']} days"
            elif data.get("is_weekend") is not None:
                result_str = f"Weekend: {data['is_weekend']}"
            else:
                result_str = "Date operation completed"
        return param_str, result_str

    def format_agent(self, result_data: Dict[str, Any]) -> str:
        """Format date results for agent action history."""
        if not result_data:
            return "No result"

        operation = result_data.get("operation", "")
        formatters = {
            "parse": lambda data: f"Parsed: {data.get('parsed', '')}",
            "format": lambda data: f"Formatted: {data.get('formatted', '')}",
            "add": lambda data: f"Added: {data.get('result', '')}",
            "subtract": lambda data: f"Subtracted: {data.get('result', '')}",
            "diff": lambda data: f"Difference: {data.get('human_readable', '')}",
            "is_weekend": lambda data: f"Is weekend: {data.get('is_weekend', '')}",
            "weekday": lambda data: f"Weekday: {data.get('weekday', '')}",
        }
        return formatters.get(operation, lambda data: "Date operation completed")(result_data)
