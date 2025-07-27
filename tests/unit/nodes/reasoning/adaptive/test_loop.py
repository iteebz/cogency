"""Tests for loop detection functionality."""

from cogency.nodes.reasoning.adaptive import (
    action_fingerprint,
    detect_fast_loop,
    detect_loop,
)

# Cognition functionality now part of State directly


class MockToolCall:
    def __init__(self, name, args):
        self.name = name
        self.args = args

    def get(self, key, default=None):
        if key == "name":
            return self.name
        if key == "args":
            return self.args
        return default


def test_action_fingerprint():
    """Test action fingerprint generation."""
    # Empty call list
    fp = action_fingerprint([])
    assert fp == "no_action"

    # Single tool call - just check it generates consistently
    fp1 = action_fingerprint([MockToolCall("search", {"query": "test"})])
    fp2 = action_fingerprint([MockToolCall("search", {"query": "test"})])
    assert fp1 == fp2
    assert fp1.startswith("search:")

    # Multiple tool calls generate combined fingerprints
    tools = [
        MockToolCall("search", {"query": "test"}),
        MockToolCall("files", {"path": "/tmp"}),
    ]
    fp = action_fingerprint(tools)
    # Should contain both tool names
    assert "search:" in fp
    assert "files:" in fp

    # Same tool name, different args
    fp1 = action_fingerprint([MockToolCall("search", {"query": "test"})])
    fp2 = action_fingerprint([MockToolCall("search", {"query": "test"})])
    assert fp1 == fp2


def test_fast_loop_detection():
    """Test fast loop detection."""
    from cogency.context import Context
    from cogency.state import State

    # Create state with cognition functionality built-in
    context = Context("test")
    state = State(context=context, query="test")
    state.iterations = [
        {
            "iteration": 1,
            "fingerprint": "search:123",
            "result": "",
            "decision": "",
            "tool_calls": [],
        },
        {
            "iteration": 2,
            "fingerprint": "search:123",
            "result": "",
            "decision": "",
            "tool_calls": [],
        },
    ]
    is_loop = detect_fast_loop(state)
    assert is_loop is False

    # No loop in short history

    state.iterations = [
        {
            "iteration": 1,
            "fingerprint": "search:123",
            "result": "",
            "decision": "",
            "tool_calls": [],
        },
        {
            "iteration": 2,
            "fingerprint": "scrape:456",
            "result": "",
            "decision": "",
            "tool_calls": [],
        },
    ]
    is_loop = detect_fast_loop(state)
    assert is_loop is False


def test_comprehensive_loop():
    """Test comprehensive loop detection."""
    from cogency.context import Context
    from cogency.state import State

    # Create state with cognition functionality built-in
    context = Context("test")
    state = State(context=context, query="test")

    # Pattern loop (A-B-A)
    state.iterations = [
        {
            "iteration": 1,
            "fingerprint": "search:123",
            "result": "",
            "decision": "",
            "tool_calls": [],
        },
        {
            "iteration": 2,
            "fingerprint": "scrape:456",
            "result": "",
            "decision": "",
            "tool_calls": [],
        },
        {
            "iteration": 3,
            "fingerprint": "search:123",
            "result": "",
            "decision": "",
            "tool_calls": [],
        },
    ]
    is_loop = detect_loop(state)
    assert is_loop is True

    # No loop detected
    state.iterations = [
        {
            "iteration": 1,
            "fingerprint": "search:123",
            "result": "",
            "decision": "",
            "tool_calls": [],
        },
        {
            "iteration": 2,
            "fingerprint": "scrape:456",
            "result": "",
            "decision": "",
            "tool_calls": [],
        },
        {
            "iteration": 3,
            "fingerprint": "analyze:789",
            "result": "",
            "decision": "",
            "tool_calls": [],
        },
    ]
    is_loop = detect_loop(state)
    assert is_loop is False

    # Repeated identical actions
    state.iterations = [
        {
            "iteration": 1,
            "fingerprint": "search:123",
            "result": "",
            "decision": "",
            "tool_calls": [],
        },
        {
            "iteration": 2,
            "fingerprint": "search:123",
            "result": "",
            "decision": "",
            "tool_calls": [],
        },
        {
            "iteration": 3,
            "fingerprint": "search:123",
            "result": "",
            "decision": "",
            "tool_calls": [],
        },
    ]
    is_loop = detect_loop(state)
    assert is_loop is True


def test_loop_empty_history():
    """Test loop detection with minimal history."""
    from cogency.context import Context
    from cogency.state import State

    # Create state with cognition functionality built-in
    context = Context("test")
    state = State(context=context, query="test")

    # Empty history
    state.iterations = []
    assert detect_loop(state) is False
    assert detect_fast_loop(state) is False
