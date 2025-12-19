"""Tool call/result serialization and parsing."""

from __future__ import annotations

import json
import re
from typing import TYPE_CHECKING, Any, TypedDict, cast

from .protocols import Tool, ToolCall, ToolResult, parse_tool_call_dict, parse_tool_result_dict

if TYPE_CHECKING:
    from collections.abc import Iterable


class ToolCallDict(TypedDict):
    name: str
    args: dict[str, Any]


class ToolResultDict(TypedDict, total=False):
    outcome: str
    content: str


class ToolParseError(ValueError):
    def __init__(self, message: str, original_json: str | None = None) -> None:
        super().__init__(message)
        self.original_json = original_json


def tool_instructions(tools: Iterable[Tool]) -> str:
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
    return json.dumps({"name": call.name, "args": call.args})


def format_result_agent(result: ToolResult) -> str:
    if result.content:
        return f"{result.outcome}\n{result.content}"
    return result.outcome


def format_results_array(calls: list[ToolCall], results: list[ToolResult]) -> str:
    array: list[dict[str, Any]] = []
    for call, result in zip(calls, results, strict=True):
        item: dict[str, Any] = {
            "tool": call.name,
            "status": "failure" if result.error else "success",
            "content": result.outcome if result.error else (result.content or result.outcome),
        }
        array.append(item)
    return json.dumps(array)


def parse_tool_call(json_str: str) -> ToolCall:
    json_str = json_str.strip()
    if "{" in json_str and "}" in json_str:
        start = json_str.find("{")
        end = json_str.rfind("}") + 1
        json_str = json_str[start:end]

    if '"""' in json_str:
        json_str = re.sub(r'"""([^"]*?)"""', r'"\1"', json_str, flags=re.DOTALL)

    try:
        raw: object = json.loads(json_str)
        call_dict = parse_tool_call_dict(raw)
        return ToolCall(name=call_dict["name"], args=call_dict["args"])
    except json.JSONDecodeError as e:
        raise ToolParseError(f"JSON parse failed: {e}", original_json=json_str) from e
    except Exception as e:
        raise ToolParseError(str(e), original_json=json_str) from e


def parse_tool_result(content: str) -> list[ToolResult]:
    try:
        raw: object = json.loads(content)
        if isinstance(raw, dict):
            data = cast("dict[str, Any]", raw)
            result_dict = parse_tool_result_dict(data)
            outcome = result_dict.get("outcome", "")
            result_content = result_dict.get("content", "")
            return [ToolResult(outcome=outcome, content=result_content)]
        if isinstance(raw, list):
            results: list[ToolResult] = []
            for item in cast("list[object]", raw):
                if isinstance(item, dict):
                    item_data = cast("dict[str, Any]", item)
                    result_dict = parse_tool_result_dict(item_data)
                    outcome = result_dict.get("outcome", "")
                    result_content = result_dict.get("content", "")
                    results.append(ToolResult(outcome=outcome, content=result_content))
            return results
    except (json.JSONDecodeError, TypeError):
        pass

    return [ToolResult(outcome=content, content="")]
