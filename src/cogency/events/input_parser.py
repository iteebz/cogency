"""Input parsing utilities for console output formatting."""

import json
import re
from typing import Any


def extract_command(input_text: Any) -> str:
    """Extract shell command from various input formats."""
    if isinstance(input_text, str):
        # Try parentheses format: "(ls -la)"
        paren_match = re.search(r"\(([^)]+)\)", input_text)
        if paren_match:
            return paren_match.group(1).strip()
        return _extract_from_string(input_text, "command")
    if isinstance(input_text, dict):
        return _extract_from_dict(input_text, "command")
    return ""


def extract_file_operation(input_text: Any) -> str:
    """Extract file operation description from input."""
    if isinstance(input_text, str):
        # Human format: "(read, demo.py)" -> "Files(read, demo.py)"
        paren_match = re.search(r"\(([^,]+),\s*([^)]+)\)", input_text)
        if paren_match:
            operation, path = paren_match.groups()
            return f"Files({operation.strip()}, {path.strip()})"
        return f"Files({_extract_from_string(input_text, 'path')})"
    if isinstance(input_text, dict):
        path = _extract_from_dict(input_text, "path")
        return f"Files({path})" if path else "Files()"
    return "Files()"


def extract_url(input_text: Any) -> str:
    """Extract URL from scrape tool input."""
    if isinstance(input_text, str):
        return _extract_from_string(input_text, "url")
    if isinstance(input_text, dict):
        return _extract_from_dict(input_text, "url")
    return ""


def extract_query(input_text: Any) -> str:
    """Extract search query from search tool input."""
    if isinstance(input_text, str):
        return _extract_from_string(input_text, "query")
    if isinstance(input_text, dict):
        return _extract_from_dict(input_text, "query")
    return ""


def _extract_from_string(input_text: str, field: str) -> str:
    """Extract field value from string input."""
    try:
        data = json.loads(input_text)
        return _extract_from_dict(data, field)
    except (json.JSONDecodeError, ValueError):
        pass

    # Direct field extraction
    pattern = rf'"{field}":\s*"([^"]+)"'
    match = re.search(pattern, input_text)
    if match:
        return match.group(1)

    # For command field, return clean string if no JSON
    if field == "command" and input_text.strip() and not input_text.startswith("{"):
        return input_text.strip()

    return ""


def _extract_from_dict(input_dict: dict[str, Any], field: str) -> str:
    """Extract field value from dictionary input."""
    if "args" in input_dict and isinstance(input_dict["args"], dict):
        value = input_dict["args"].get(field, "")
    else:
        value = input_dict.get(field, "")

    return str(value) if value else ""
