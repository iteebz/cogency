"""System context tests."""

from cogency.context.system import system


def test_format_basic():
    """Basic system prompt formatting."""
    result = system.format()

    assert isinstance(result, str)
    assert len(result) > 0


def test_format_with_tools():
    """System prompt with tools."""

    class MockTool:
        name = "test_tool"
        description = "test description"

    tools = {"test_tool": MockTool()}
    result = system.format(tools)

    assert "test_tool" in result
