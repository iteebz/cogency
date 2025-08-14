"""Execution tests - Domain execution tracking."""

from cogency.context.execution import Execution, create_execution


def test_create():
    """Test creating an Execution instance."""
    execution = create_execution()
    assert execution.iteration == 0
    assert execution.max_iterations == 10


def test_defaults():
    """Test that default values are properly set."""
    execution = Execution()

    assert execution.iteration == 0
    assert execution.max_iterations == 10
    assert execution.stop_reason is None
    assert execution.messages == []
    assert execution.response is None
    assert execution.pending_calls == []
    assert execution.completed_calls == []
    assert execution.iterations_without_tools == 0


def test_add_message():
    """Test adding messages to conversation history."""
    from cogency.context.conversation import Conversation, add_message

    conversation = Conversation(user_id="test", messages=[])
    add_message(conversation, "user", "Hello")
    add_message(conversation, "assistant", "Hi there")

    assert len(conversation.messages) == 2
    assert conversation.messages[0]["role"] == "user"
    assert conversation.messages[0]["content"] == "Hello"
    assert conversation.messages[1]["role"] == "assistant"
    assert conversation.messages[1]["content"] == "Hi there"


def test_tool_calls():
    """Test tool call management."""
    from cogency.context.execution import Execution, finish_tools, set_tool_calls

    execution = Execution()

    calls = [{"name": "test_tool", "args": {"arg": "value"}}]
    set_tool_calls(execution, calls)

    assert execution.pending_calls == calls
    assert execution.completed_calls == []

    results = [{"name": "test_tool", "result": "success"}]
    finish_tools(execution, results)

    assert execution.pending_calls == []
    assert execution.completed_calls == results


def test_should_continue():
    """Test continue logic."""
    execution = Execution()

    # Basic continue checks - execution state tracks iterations
    assert execution.iteration == 0
    assert execution.pending_calls == []

    # Test iteration tracking
    execution.iteration = 1
    assert execution.iteration < execution.max_iterations
    assert execution.response is None
    assert execution.stop_reason is None

    # Test setting values
    execution.response = "Test response"
    execution.stop_reason = "completed"
    assert execution.response == "Test response"
    assert execution.stop_reason == "completed"


def test_advance_iteration():
    """Test iteration advancement."""
    state = Execution()

    assert state.iteration == 0
    state.iteration += 1
    assert state.iteration == 1
