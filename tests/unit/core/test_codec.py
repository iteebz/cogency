import json

import pytest

from cogency.core.codec import (
    format_call_agent,
    format_result_agent,
    parse_tool_call,
    parse_tool_result,
    tool_instructions,
)
from cogency.core.protocols import ToolCall, ToolResult


def test_valid_json():
    result = parse_tool_call('{"name": "write", "args": {"file": "test.txt"}}')
    assert result.name == "write"
    assert result.args["file"] == "test.txt"


def test_extra_data():
    result = parse_tool_call('prefix{"name": "tool", "args": {}}suffix')
    assert result.name == "tool"


def test_unquoted_keys():
    with pytest.raises(ValueError):
        parse_tool_call('{"name": "tool", args: {key: "val"}}')


def test_missing_colon():
    with pytest.raises(ValueError):
        parse_tool_call('{"name": "tool", "args" {"key": "val"}}')


def test_complex_fails():
    with pytest.raises(ValueError):
        parse_tool_call('{"name": "w", "args": {"c": "unclosed string}}')


def test_result_dict():
    results = parse_tool_result('{"outcome": "ok", "content": "data"}')
    assert len(results) == 1
    assert results[0].outcome == "ok"
    assert results[0].content == "data"


def test_result_list():
    results = parse_tool_result('[{"outcome": "ok", "content": "data"}]')
    assert len(results) == 1
    assert results[0].outcome == "ok"


def test_result_string_fallback():
    results = parse_tool_result("plain text")
    assert len(results) == 1
    assert results[0].outcome == "plain text"
    assert results[0].content == ""


def test_result_malformed_json():
    results = parse_tool_result("{bad json}")
    assert len(results) == 1
    assert results[0].outcome == "{bad json}"


def test_tool_instructions(mock_tool):
    tool_instance = mock_tool()
    tool_instance.configure(
        name="mock",
        description="Mock tool",
        schema={"arg1": {"required": True}, "arg2": {"required": False}},
    )
    tools = [tool_instance]
    result = tool_instructions(tools)
    assert "mock(arg1, arg2?) - Mock tool" in result


def test_format_call_agent():
    call = ToolCall(name="write", args={"file": "test.txt", "content": "data"})
    result = format_call_agent(call)
    parsed = json.loads(result)
    assert parsed["name"] == "write"
    assert parsed["args"]["file"] == "test.txt"


def test_format_result_agent():
    result_with_content = ToolResult(outcome="Success", content="file written")
    assert format_result_agent(result_with_content) == "Success\nfile written"

    result_no_content = ToolResult(outcome="Done", content="")
    assert format_result_agent(result_no_content) == "Done"
