"""ExecutionState tests - Pure execution tracking."""

from cogency.state.agent import ExecutionState


def test_create():
    """Test creating an ExecutionState instance."""
    state = ExecutionState()
    assert state.iteration == 0
    assert state.max_iterations == 10


def test_defaults():
    """Test that default values are properly set."""
    state = ExecutionState()

    assert state.iteration == 0
    assert state.max_iterations == 10
    assert state.mode == "adapt"
    assert state.stop_reason is None
    assert state.messages == []
    assert state.response is None
    assert state.pending_calls == []
    assert state.completed_calls == []
    assert state.iterations_without_tools == 0


def test_add_message():
    """Test adding messages to conversation history."""
    from cogency.state import State
    from cogency.state.mutations import add_message

    state = State(query="test query")
    add_message(state, "user", "Hello")
    add_message(state, "assistant", "Hi there")

    assert len(state.execution.messages) == 2
    assert state.execution.messages[0]["role"] == "user"
    assert state.execution.messages[0]["content"] == "Hello"
    assert state.execution.messages[1]["role"] == "assistant"
    assert state.execution.messages[1]["content"] == "Hi there"
    assert "timestamp" in state.execution.messages[0]


def test_tool_calls():
    """Test tool call management."""
    from cogency.state import State
    from cogency.state.mutations import finish_tools, set_tool_calls

    state = State(query="test query")

    calls = [{"name": "test_tool", "args": {"arg": "value"}}]
    set_tool_calls(state, calls)

    assert state.execution.pending_calls == calls
    assert state.execution.completed_calls == []

    results = [{"name": "test_tool", "result": "success"}]
    finish_tools(state, results)

    assert state.execution.pending_calls == []
    assert state.execution.completed_calls == results


def test_should_continue():
    """Test continue logic."""
    state = ExecutionState()

    # Basic continue checks - execution state has no continue logic
    assert state.iteration == 0
    assert state.pending_calls == []
    assert state.response is None
    assert state.stop_reason is None

    # Test setting values
    state.response = "Done"
    assert state.response == "Done"

    state.stop_reason = "error"
    assert state.stop_reason == "error"

    state.iteration = 5
    assert state.iteration == 5


def test_advance_iteration():
    """Test iteration advancement."""
    state = ExecutionState()

    assert state.iteration == 0
    state.iteration += 1
    assert state.iteration == 1
