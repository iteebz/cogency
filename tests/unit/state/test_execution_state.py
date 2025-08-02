"""ExecutionState tests - Pure execution tracking."""

from cogency.state.execution import ExecutionState


def test_create():
    """Test creating an ExecutionState instance."""
    state = ExecutionState(query="test query")
    assert state.query == "test query"
    assert state.user_id == "default"


def test_defaults():
    """Test that default values are properly set."""
    state = ExecutionState(query="test query")

    assert state.user_id == "default"
    assert state.iteration == 0
    assert state.max_iterations == 10
    assert state.mode == "adapt"
    assert state.stop_reason is None
    assert state.messages == []
    assert state.response is None
    assert state.pending_calls == []
    assert state.completed_calls == []
    assert state.debug is False
    assert state.notifications == []


def test_add_message():
    """Test adding messages to conversation history."""
    state = ExecutionState(query="test query")

    state.add_message("user", "Hello")
    state.add_message("assistant", "Hi there")

    assert len(state.messages) == 2
    assert state.messages[0]["role"] == "user"
    assert state.messages[0]["content"] == "Hello"
    assert state.messages[1]["role"] == "assistant"
    assert state.messages[1]["content"] == "Hi there"
    assert "timestamp" in state.messages[0]


def test_tool_calls():
    """Test tool call management."""
    state = ExecutionState(query="test query")

    calls = [{"name": "test_tool", "args": {"param": "value"}}]
    state.set_tool_calls(calls)

    assert state.pending_calls == calls
    assert state.completed_calls == []

    results = [{"name": "test_tool", "result": "success"}]
    state.complete_tool_calls(results)

    assert state.pending_calls == []
    assert state.completed_calls == results


def test_should_continue():
    """Test continue logic."""
    state = ExecutionState(query="test query")

    # Should not continue without pending calls
    assert not state.should_continue()

    # Should continue with pending calls
    state.set_tool_calls([{"name": "test"}])
    assert state.should_continue()

    # Should not continue with response set
    state.response = "Done"
    assert not state.should_continue()

    # Should not continue with stop reason
    state.response = None
    state.stop_reason = "error"
    assert not state.should_continue()

    # Should not continue at max iterations
    state.stop_reason = None
    state.iteration = 10
    assert not state.should_continue()


def test_advance_iteration():
    """Test iteration advancement."""
    state = ExecutionState(query="test query")

    assert state.iteration == 0
    state.advance_iteration()
    assert state.iteration == 1
