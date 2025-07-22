"""Simple CSV tool - read, write, append. Agent handles logic."""

import csv
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from .base import BaseTool
from .registry import tool


@tool
class CSV(BaseTool):
    """Simple CSV operations - smart agent, dumb tool."""

    def __init__(self):
        super().__init__(
            name="csv",
            description="Read, write, and append CSV files",
            emoji="📊",
            rules=(
                "EXPORT ONLY: Save computed results to CSV format. "
                "NEVER use for analysis or calculations - use 'code' tool first for all computational work, "
                "then optionally use this to export final results to CSV format."
            ),
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
            return {"error": f"Invalid operation: {operation}. Use: read, write, append"}

    def _get_absolute_path(self, file_path: str) -> Path:
        """Get absolute path relative to project root."""
        return Path(os.getcwd()) / file_path

    def _read(self, file_path: str) -> Dict[str, Any]:
        """Read CSV file."""
        try:
            path = self._get_absolute_path(file_path)
            if not path.exists():
                return {"error": f"File not found: {file_path}"}

            with open(path, newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                data = list(reader)

            return {"success": True, "data": data, "row_count": len(data)}
        except Exception as e:
            return {"error": f"Read failed: {str(e)}"}

    def _write(self, file_path: str, data: Optional[List[Dict]]) -> Dict[str, Any]:
        """Write CSV file."""
        try:
            if not data:
                return {"error": "No data provided"}

            path = self._get_absolute_path(file_path)
            path.parent.mkdir(parents=True, exist_ok=True)

            with open(path, "w", newline="", encoding="utf-8") as f:
                if data:
                    writer = csv.DictWriter(f, fieldnames=data[0].keys())
                    writer.writeheader()
                    writer.writerows(data)

            return {"success": True, "rows_written": len(data)}
        except Exception as e:
            return {"error": f"Write failed: {str(e)}"}

    def _append(self, file_path: str, data: Optional[List[Dict]]) -> Dict[str, Any]:
        """Append to CSV file."""
        try:
            if not data:
                return {"error": "No data provided"}

            path = self._get_absolute_path(file_path)
            
            if not path.exists():
                return self._write(file_path, data)

            with open(path, "a", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=data[0].keys())
                writer.writerows(data)

            return {"success": True, "rows_appended": len(data)}
        except Exception as e:
            return {"error": f"Append failed: {str(e)}"}

    def schema(self) -> str:
        """Return tool schema."""
        return "csv(operation='read|write|append', file_path='string', data=list_of_dicts)"

    def examples(self) -> List[str]:
        """Return examples."""
        return [
            "csv(operation='read', file_path='data.csv')",
            "csv(operation='write', file_path='output.csv', data=[{'name': 'John', 'age': 30}])",
            "csv(operation='append', file_path='logs.csv', data=[{'event': 'login', 'time': '10:00'}])",
        ]

    def format_params(self, params: Dict[str, Any]) -> str:
        """Format parameters for display."""
        op = params.get("operation", "")
        file_path = params.get("file_path", "")
        return f"({op}: {Path(file_path).name})" if op and file_path else ""