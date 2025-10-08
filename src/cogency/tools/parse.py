import json
import re

from ..core.exceptions import ProtocolError
from ..core.protocols import ToolCall, ToolResult


def _auto_escape_content(json_str: str) -> str:
    """Escape unescaped content in JSON strings."""
    content_start = json_str.find('"content": "')
    if content_start == -1:
        return json_str

    value_start = content_start + len('"content": "')
    i = value_start
    bracket_depth = 0

    while i < len(json_str):
        char = json_str[i]
        if char == "{":
            bracket_depth += 1
        elif char == "}":
            bracket_depth -= 1
        elif (
            char == '"' and i + 1 < len(json_str) and json_str[i + 1] in ",}" and bracket_depth <= 0
        ):
            break
        i += 1

    if i >= len(json_str):
        return json_str

    content = json_str[value_start:i]
    escaped = (
        content.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\n", "\\n")
        .replace("\r", "\\r")
        .replace("\t", "\\t")
    )

    return json_str[:value_start] + escaped + json_str[i:]


def parse_tool_call(json_str: str) -> ToolCall:
    """Parse ToolCall from JSON with minimal error recovery."""
    json_str = json_str.strip()
    if "{" in json_str and "}" in json_str:
        start = json_str.find("{")
        end = json_str.rfind("}") + 1
        json_str = json_str[start:end]

    if '"""' in json_str:
        json_str = re.sub(r'"""([^"]*?)"""', r'"\1"', json_str, flags=re.DOTALL)

    try:
        json.loads(json_str)
    except json.JSONDecodeError:
        json_str = _auto_escape_content(json_str)

    try:
        data = json.loads(json_str)
        return ToolCall(name=data["name"], args=data.get("args", {}))
    except json.JSONDecodeError as e:
        raise ProtocolError(f"JSON parse failed: {e}", original_json=json_str) from e

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

    return [ToolResult(outcome=content, content="")]
