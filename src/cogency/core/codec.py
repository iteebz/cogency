"""Codec utilities for tool calls/results.

Provides both serialization (formatting) helpers for model prompts
and parsing helpers to recover structured objects from LLM output.
"""

from __future__ import annotations

import json
import re
from collections.abc import Iterable

from .protocols import Tool, ToolCall, ToolResult


class ToolParseError(ValueError):
    """Raised when tool output cannot be parsed safely."""

    def __init__(self, message: str, original_json: str | None = None) -> None:
        super().__init__(message)
        self.original_json = original_json


def tool_instructions(tools: Iterable[Tool]) -> str:
    """Generate dynamic tool instructions for LLM context."""
    lines: list[str] = []

    for tool in tools:
        params: list[str] = []
        schema = getattr(tool, "schema", {}) or {}
        for param, info in schema.items():
            params.append(param if info.get("required", True) else f"{param}?")
        param_str = ", ".join(params)
        lines.append(f"{tool.name}({param_str}) - {tool.description}")

    return "TOOLS:\n" + "\n".join(lines)


def format_call_agent(call: ToolCall) -> str:
    """Serialize a ToolCall for agent consumption."""
    return json.dumps({"name": call.name, "args": call.args})


def format_result_agent(result: ToolResult) -> str:
    """Serialize a ToolResult for agent consumption."""
    if result.content:
        return f"{result.outcome}\n{result.content}"
    return result.outcome


def _auto_escape_content(json_str: str) -> str:
    """Escape unescaped content in JSON strings."""
    content_start = json_str.find('"content": "')
    if content_start == -1:
        return json_str

    value_start = content_start + len('"content": "')
    i = value_start
    escaped = False

    while i < len(json_str):
        char = json_str[i]

        if escaped:
            escaped = False
            i += 1
            continue

        if char == "\\":
            escaped = True
            i += 1
            continue

        if char == '"':
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
        raise ToolParseError(f"JSON parse failed: {e}", original_json=json_str) from e
    except KeyError as e:
        raise ToolParseError(f"Missing required field: {e}", original_json=json_str) from e


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
