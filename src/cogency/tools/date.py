"""Date tool - focused date operations with zero network dependencies."""

import logging
from datetime import timedelta
from typing import Any, Dict, List

import pytz
from dateutil import parser as date_parser

from cogency.errors import ToolError, ValidationError

from .base import BaseTool
from .registry import tool

logger = logging.getLogger(__name__)


@tool
class Date(BaseTool):
    """Date operations: parsing, formatting, arithmetic, weekday calculations."""

    def __init__(self):
        super().__init__(
            name="date",
            description="Date operations: parsing, formatting, arithmetic, weekday calculations",
            emoji="📅",
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

    async def run(self, operation: str = "parse", **kwargs) -> Dict[str, Any]:
        """Execute date operation.

        Args:
            operation: Operation to perform (parse, format, add, subtract, diff, is_weekend, weekday)
            **kwargs: Operation-specific parameters

        Returns:
            Operation result with date data
        """
        if operation not in self._operations:
            raise ValidationError(
                f"Unknown operation: {operation}. Available: {list(self._operations.keys())}"
            )

        return await self._operations[operation](**kwargs)

    async def _parse(self, date_string: str, timezone: str = None) -> Dict[str, Any]:
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

            return {
                "original": date_string,
                "parsed": parsed.date().isoformat(),
                "weekday": parsed.strftime("%A"),
                "is_weekend": parsed.weekday() >= 5,
                "day_of_year": parsed.timetuple().tm_yday,
                "week_number": int(parsed.strftime("%W")),
            }
        except Exception as e:
            raise ToolError(f"Failed to parse date string '{date_string}': {str(e)}") from None

    async def _format(self, date_str: str, format: str) -> Dict[str, Any]:
        """Format date string."""
        try:
            dt = date_parser.parse(date_str)
            formatted = dt.strftime(format)

            return {"original": date_str, "format": format, "formatted": formatted}
        except Exception as e:
            raise ToolError(f"Failed to format date: {str(e)}") from None

    async def _add(self, date_str: str, **kwargs) -> Dict[str, Any]:
        """Add time to date."""
        try:
            dt = date_parser.parse(date_str)

            delta_kwargs = {}
            for key in ["days", "weeks"]:
                if key in kwargs:
                    delta_kwargs[key] = kwargs[key]

            if not delta_kwargs:
                raise ValidationError("No time units provided. Use days or weeks.")

            delta = timedelta(**delta_kwargs)
            result_dt = dt + delta

            return {
                "original": date_str,
                "added": delta_kwargs,
                "result": result_dt.date().isoformat(),
                "weekday": result_dt.strftime("%A"),
                "is_weekend": result_dt.weekday() >= 5,
            }
        except Exception as e:
            raise ToolError(f"Failed to add time: {str(e)}") from None

    async def _subtract(self, date_str: str, **kwargs) -> Dict[str, Any]:
        """Subtract time from date."""
        try:
            dt = date_parser.parse(date_str)

            delta_kwargs = {}
            for key in ["days", "weeks"]:
                if key in kwargs:
                    delta_kwargs[key] = kwargs[key]

            if not delta_kwargs:
                raise ValidationError("No time units provided. Use days or weeks.")

            delta = timedelta(**delta_kwargs)
            result_dt = dt - delta

            return {
                "original": date_str,
                "subtracted": delta_kwargs,
                "result": result_dt.date().isoformat(),
                "weekday": result_dt.strftime("%A"),
                "is_weekend": result_dt.weekday() >= 5,
            }
        except Exception as e:
            raise ToolError(f"Failed to subtract time: {str(e)}") from None

    async def _diff(self, start_date: str, end_date: str) -> Dict[str, Any]:
        """Calculate difference between two dates."""
        try:
            start = date_parser.parse(start_date)
            end = date_parser.parse(end_date)

            diff = end.date() - start.date()

            return {
                "start": start_date,
                "end": end_date,
                "days": diff.days,
                "weeks": diff.days // 7,
                "human_readable": f"{diff.days} days",
            }
        except Exception as e:
            raise ToolError(f"Failed to calculate difference: {str(e)}") from None

    async def _is_weekend(self, date_str: str) -> Dict[str, Any]:
        """Check if date falls on weekend."""
        try:
            dt = date_parser.parse(date_str)
            is_weekend = dt.weekday() >= 5

            return {
                "date": date_str,
                "is_weekend": is_weekend,
                "weekday": dt.strftime("%A"),
                "weekday_number": dt.weekday(),
            }
        except Exception as e:
            raise ToolError(f"Failed to check weekend: {str(e)}") from None

    async def _weekday(self, date_str: str) -> Dict[str, Any]:
        """Get weekday information."""
        try:
            dt = date_parser.parse(date_str)

            return {
                "date": date_str,
                "weekday": dt.strftime("%A"),
                "weekday_short": dt.strftime("%a"),
                "weekday_number": dt.weekday(),
                "is_weekend": dt.weekday() >= 5,
            }
        except Exception as e:
            raise ToolError(f"Failed to get weekday: {str(e)}") from None

    def schema(self) -> str:
        return "date(operation='parse|format|add|subtract|diff|is_weekend|weekday', **kwargs)"

    def examples(self) -> List[str]:
        return [
            "date(operation='parse', date_string='2024-01-15')",
            "date(operation='format', date_str='2024-01-15', format='%B %d, %Y')",
            "date(operation='add', date_str='2024-01-15', days=7)",
            "date(operation='diff', start_date='2024-01-15', end_date='2024-01-20')",
            "date(operation='is_weekend', date_str='2024-01-15')",
        ]
