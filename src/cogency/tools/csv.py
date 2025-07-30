"""Simple CSV tool - read, write, append. Agent handles logic."""

import csv
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from resilient_result import Result

from cogency.tools.base import Tool
from cogency.tools.registry import tool

logger = logging.getLogger(__name__)


@dataclass
class CSVArgs:
    operation: str
    file_path: str
    data: Optional[List[Dict]] = None


@tool
class CSV(Tool):
    """Simple CSV operations - smart agent, dumb tool."""

    def __init__(self):
        super().__init__(
            name="csv",
            description="Read, write, and append CSV files",
            schema="csv(operation='read'|'write'|'append', file_path=str, data=list)",
            emoji="📊",
            params=CSVArgs,
            examples=[
                "csv(operation='read', file_path='data.csv')",
                "csv(operation='write', file_path='output.csv', data=[{'name': 'John', 'age': 30}])",
            ],
            rules=[
                "Use code tool for analysis, then export results here",
            ],
        )

    async def run(
        self,
        operation: str,
        file_path: str,
        data: Optional[List[Dict]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Execute CSV operation.

        Args:
            operation: 'read', 'write', or 'append'
            file_path: Path to CSV file
            data: Data for write/append (list of dicts)
        """
        if operation == "read":
            return self._read(file_path)
        elif operation == "write":
            return self._write(file_path, data)
        elif operation == "append":
            return self._append(file_path, data)
        else:
            return Result.fail(f"Invalid operation: {operation}. Use: read, write, append")

    def _get_absolute_path(self, file_path: str) -> Path:
        """Get absolute path relative to project root."""
        return Path(os.getcwd()) / file_path

    def _read(self, file_path: str) -> Dict[str, Any]:
        """Read CSV file."""
        try:
            path = self._get_absolute_path(file_path)
            if not path.exists():
                return Result.fail(f"File not found: {file_path}")

            with open(path, newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                data = list(reader)

            return Result.ok({"data": data, "row_count": len(data)})
        except Exception as e:
            return Result.fail(f"Read failed: {str(e)}")

    def _write(self, file_path: str, data: Optional[List[Dict]]) -> Dict[str, Any]:
        """Write CSV file."""
        try:
            path = self._get_absolute_path(file_path)
            path.parent.mkdir(parents=True, exist_ok=True)

            with open(path, "w", newline="", encoding="utf-8") as f:
                if data:
                    writer = csv.DictWriter(f, fieldnames=data[0].keys())
                    writer.writeheader()
                    writer.writerows(data)

            return Result.ok({"rows_written": len(data)})
        except Exception as e:
            logger.error(f"CSV write failed for {file_path}: {e}")
            return Result.fail(f"Write failed: {str(e)}")

    def _append(self, file_path: str, data: Optional[List[Dict]]) -> Dict[str, Any]:
        """Append to CSV file."""
        try:
            path = self._get_absolute_path(file_path)

            if not path.exists():
                return self._write(file_path, data)

            with open(path, "a", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=data[0].keys())
                writer.writerows(data)

            return Result.ok({"rows_appended": len(data)})
        except Exception as e:
            return Result.fail(f"Append failed: {str(e)}")

    def format_human(
        self, params: Dict[str, Any], results: Optional[Result] = None
    ) -> tuple[str, str]:
        """Format CSV execution for display."""
        op = params.get("operation", "")
        file_path = params.get("file_path", "")
        param_str = f"({op}: {Path(file_path).name})" if op and file_path else ""

        if results is None:
            return param_str, ""

        # Format results
        if results.failure:
            result_str = f"Error: {results.error}"
        else:
            data = results.data
            if op == "read":
                count = data.get("row_count", 0)
                result_str = f"Read {count} rows"
            elif op == "write":
                count = data.get("rows_written", 0)
                result_str = f"Wrote {count} rows"
            elif op == "append":
                count = data.get("rows_appended", 0)
                result_str = f"Appended {count} rows"
            else:
                result_str = "Operation completed"

        return param_str, result_str

    def format_agent(self, result_data: Dict[str, Any]) -> str:
        """Format CSV results for agent action history."""
        if not result_data:
            return "No result"

        operation = result_data.get("operation", "")
        formatters = {
            "read": lambda data: f"Read {data.get('row_count', 0)} rows from {data.get('file_path', '')}",
            "write": lambda data: f"Wrote {data.get('rows_written', 0)} rows to {data.get('file_path', '')}",
            "append": lambda data: f"Appended {data.get('rows_appended', 0)} rows to {data.get('file_path', '')}",
        }
        return formatters.get(operation, lambda data: "CSV operation completed")(result_data)
