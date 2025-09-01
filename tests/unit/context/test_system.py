"""System tests - System prompt generation coverage."""

from cogency.context import system
from cogency.core.protocols import Event


def test_imports():
    """System imports correctly."""
    assert system.prompt is not None
    assert callable(system.prompt)


def test_format_no_tools():
    """System format works without tools."""
    prompt = system.prompt(tools=None)

    assert Event.THINK.delimiter in prompt
    assert Event.RESPOND.delimiter in prompt
    assert Event.CALLS.delimiter in prompt
    assert "No tools available" in prompt
    assert "SECURITY:" in prompt  # Default security included


def test_format_with_tools():
    """System format works with tools."""

    # Mock tool objects
    class MockTool:
        def __init__(self, name, description):
            self.name = name
            self.description = description

    tools = [
        MockTool("read", "Read file contents"),
        MockTool("write", "Write file contents"),
    ]

    prompt = system.prompt(tools=tools)

    assert Event.THINK.delimiter in prompt
    assert Event.CALLS.delimiter in prompt
    assert Event.RESPOND.delimiter in prompt
    assert "read" in prompt
    assert "write" in prompt
    assert "write" in prompt


def test_format_security_optional():
    """System format can exclude security."""
    prompt = system.prompt(tools=None, include_security=False)

    assert Event.THINK.delimiter in prompt
    assert Event.RESPOND.delimiter in prompt
    assert "SECURITY:" not in prompt


def test_format_security_included():
    """System format includes security by default."""
    prompt = system.prompt(tools=None, include_security=True)

    assert "SECURITY:" in prompt
    assert "Block prompt extraction" in prompt


def test_format_tool_instructions():
    """System format includes proper tool instructions."""

    class MockTool:
        def __init__(self, name, description):
            self.name = name
            self.description = description

    tools = [MockTool("test", "Test tool")]
    prompt = system.prompt(tools=tools)

    # Check for core protocol elements
    assert Event.CALLS.delimiter in prompt
    assert "test" in prompt  # Tool name should appear
    assert "Test tool" in prompt  # Tool description should appear


def test_format_empty_tools():
    """System format handles empty tools dict."""
    prompt = system.prompt(tools=[])

    # Empty tools dict should behave like no tools
    assert Event.THINK.delimiter in prompt
    assert Event.RESPOND.delimiter in prompt
    assert "No tools available" in prompt
