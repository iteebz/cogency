"""System tests."""

from cogency.context import system
from cogency.core.protocols import Event


class MockTool:
    def __init__(self, name, description):
        self.name = name
        self.description = description


def test_prompt():
    """System prompt contains delimiters, handles tools/security correctly."""
    # No tools
    prompt = system.prompt(tools=None)
    assert Event.THINK.delimiter in prompt
    assert Event.CALLS.delimiter in prompt
    assert Event.RESPOND.delimiter in prompt
    assert Event.END.delimiter in prompt
    assert "No tools available" in prompt
    assert "MANDATORY SECURITY RESPONSE PATTERN:" in prompt

    # With tools
    tools = [MockTool("read", "Read file contents")]
    prompt = system.prompt(tools=tools)
    assert "read" in prompt
    assert "Read file contents" in prompt

    # Empty tools
    prompt = system.prompt(tools=[])
    assert "No tools available" in prompt

    # Security optional
    prompt = system.prompt(tools=None, include_security=False)
    assert "SECURITY PROTOCOL:" not in prompt
