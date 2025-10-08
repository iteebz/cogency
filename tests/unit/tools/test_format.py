import json

from cogency.core.protocols import Tool, ToolCall, ToolResult
from cogency.tools.format import format_call_agent, format_result_agent, tool_instructions


class Mock(Tool):
    name = "mock"
    description = "Mock tool"
    schema = {"arg1": {"required": True}, "arg2": {"required": False}}

    def describe(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "schema": self.schema,
        }

    async def execute(self, **kwargs):
        return ToolResult(outcome="ok")


def test_tool_instructions():
    tools = [Mock()]
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
