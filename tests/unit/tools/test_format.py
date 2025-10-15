import json

from cogency.core.codec import format_call_agent, format_result_agent, tool_instructions
from cogency.core.protocols import ToolCall, ToolResult


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
