"""Tool parsing - minimal resilience for common LLM errors."""

import json
import re

from ..core.exceptions import ProtocolError
from ..core.protocols import ToolCall, ToolResult


def _auto_escape_content(json_str: str) -> str:
    """Auto-escape content in JSON strings - handle LLM escaping failures."""
    # Find "content": " and extract until the structural closing quote
    content_start = json_str.find('"content": "')
    if content_start == -1:
        return json_str  # No content field found

    # Start after "content": "
    value_start = content_start + len('"content": "')

    # Find the structural closing quote by looking for ", or "} patterns
    # This handles unescaped quotes within the content itself
    i = value_start
    bracket_depth = 0
    while i < len(json_str):
        char = json_str[i]

        # Track bracket depth to handle nested objects/arrays in content
        if char == "{":
            bracket_depth += 1
        elif char == "}":
            bracket_depth -= 1

        # Look for the closing quote followed by , or }
        if char == '"' and i + 1 < len(json_str):
            next_char = json_str[i + 1]
            # This looks like a field terminator
            if next_char in ",}" and bracket_depth <= 0:
                break  # Found structural closing quote

        i += 1

    if i >= len(json_str):
        return json_str  # No closing quote found, malformed

    # Extract the content between the quotes
    content = json_str[value_start:i]

    # Escape the content properly
    escaped_content = (
        content.replace("\\", "\\\\")  # Escape backslashes first
        .replace('"', '\\"')  # Escape quotes
        .replace("\n", "\\n")  # Escape newlines
        .replace("\r", "\\r")  # Escape carriage returns
        .replace("\t", "\\t")
    )  # Escape tabs

    # Replace the content in the original string
    before = json_str[:value_start]
    after = json_str[i:]  # From closing quote onwards

    return before + escaped_content + after


def parse_tool_call(json_str: str) -> ToolCall:
    """Parse ToolCall from JSON string with minimal error recovery."""
    # Extract JSON if surrounded by text
    json_str = json_str.strip()
    if "{" in json_str and "}" in json_str:
        start = json_str.find("{")
        end = json_str.rfind("}") + 1
        json_str = json_str[start:end]

    # Pre-fix triple quotes and unescaped content before parsing
    if '"""' in json_str:
        json_str = re.sub(r'"""([^"]*?)"""', r'"\1"', json_str, flags=re.DOTALL)

    # Auto-escape common content issues in "content" fields if JSON is malformed
    try:
        # Test if JSON is already valid - if so, don't auto-escape
        json.loads(json_str)
    except json.JSONDecodeError:
        # JSON is malformed, try auto-escape
        json_str = _auto_escape_content(json_str)

    # Try direct parsing first
    try:
        data = json.loads(json_str)
        return ToolCall(name=data["name"], args=data.get("args", {}))
    except json.JSONDecodeError as e:
        # Only handle the most common failures
        error_msg = str(e)

        # Fix unquoted keys: {key: "value"} -> {"key": "value"}
        if "Expecting property name" in error_msg:
            json_str = re.sub(r"([{,]\s*)(\w+)(\s*:)", r'\1"\2"\3', json_str)

        # Fix missing colon: {"key" "value"} -> {"key": "value"}
        elif "Expecting ':' delimiter" in error_msg:
            json_str = re.sub(r'("\w+")\s+({)', r"\1: \2", json_str)

        # Fix control characters: newlines in strings
        elif "Invalid control character" in error_msg:
            json_str = json_str.replace("\n", "\\n").replace("\t", "\\t").replace("\r", "\\r")

        # Handle multiple JSON objects concatenated (take the first one)
        elif "Extra data" in error_msg:
            try:
                decoder = json.JSONDecoder()
                data, end = decoder.raw_decode(json_str)
                # If raw_decode succeeds, we've got the first object.
                # We'll then proceed to parse this 'data'
                return ToolCall(name=data["name"], args=data.get("args", {}))
            except json.JSONDecodeError:
                # If raw_decode itself fails, then the string is still malformed
                pass  # Fall through to raise ProtocolError

        else:
            raise ProtocolError(f"JSON parse failed: {error_msg}", original_json=json_str) from e

        # Retry once
        try:
            data = json.loads(json_str)
            return ToolCall(name=data["name"], args=data.get("args", {}))
        except (json.JSONDecodeError, KeyError) as retry_e:
            raise ProtocolError(
                f"JSON repair failed: {retry_e}", original_json=json_str
            ) from retry_e

    except KeyError as e:
        raise ProtocolError(f"Missing required field: {e}", original_json=json_str) from e


def parse_tool_result(content: str) -> list[ToolResult]:
    """Parse tool result from JSON string."""
    try:
        data = json.loads(content)
        if isinstance(data, dict):
            return [ToolResult(outcome=data.get("outcome", ""), content=data.get("content", ""))]
        if isinstance(data, list):
            return [
                ToolResult(outcome=item.get("outcome", ""), content=item.get("content", ""))
                for item in data
                if isinstance(item, dict)
            ]
    except (json.JSONDecodeError, TypeError):
        pass

    # Fallback: treat as plain text
    return [ToolResult(outcome=content, content="")]
