"""State mutations tests."""

from datetime import datetime

from cogency.state import State
from cogency.state.mutations import add_message, update_from_reasoning


def test_add_message_basic():
    state = State(query="test query")

    add_message(state, "user", "hello world")

    assert len(state.conversation.messages) == 1
    message = state.conversation.messages[0]
    assert message["role"] == "user"
    assert message["content"] == "hello world"

    assert isinstance(state.conversation.last_updated, datetime)

    assert len(state.execution.messages) == 1
    assert state.execution.messages[0]["content"] == "hello world"

    assert isinstance(state.last_updated, datetime)


def test_add_message_multiple():
    state = State(query="test query")

    add_message(state, "user", "first message")
    add_message(state, "assistant", "second message")
    add_message(state, "user", "third message")

    assert len(state.conversation.messages) == 3
    assert state.conversation.messages[0]["content"] == "first message"
    assert state.conversation.messages[1]["content"] == "second message"
    assert state.conversation.messages[2]["content"] == "third message"

    assert len(state.execution.messages) == 3
    assert state.execution.messages[0]["role"] == "user"
    assert state.execution.messages[1]["role"] == "assistant"
    assert state.execution.messages[2]["role"] == "user"


def test_add_message_preserves():
    state = State(query="test query")

    state.conversation.messages = [
        {"role": "user", "content": "existing message", "timestamp": "2023-01-01T00:00:00"}
    ]

    add_message(state, "assistant", "new message")

    assert len(state.conversation.messages) == 2
    assert state.conversation.messages[0]["content"] == "existing message"
    assert state.conversation.messages[1]["content"] == "new message"


def test_add_message_timestamps():
    """Test that conversation-level timestamps are still tracked."""
    state = State(query="test query")

    add_message(state, "user", "test message")

    # Message objects no longer have timestamps - clean OpenAI format
    message = state.conversation.messages[0]
    assert "timestamp" not in message
    assert message["role"] == "user"
    assert message["content"] == "test message"

    # But conversation-level timestamps are still maintained
    assert isinstance(state.conversation.last_updated, datetime)
    assert isinstance(state.last_updated, datetime)


def test_update_from_reasoning_response():
    state = State(query="test query")
    reasoning_result = {"response": "Test response from reasoning"}

    update_from_reasoning(state, reasoning_result)

    assert state.execution.response == "Test response from reasoning"
    assert isinstance(state.last_updated, datetime)


def test_update_from_reasoning_actions():
    state = State(query="test query")
    reasoning_result = {"actions": ["action1", "action2", "action3"]}

    update_from_reasoning(state, reasoning_result)

    assert state.execution.pending_calls == ["action1", "action2", "action3"]


def test_update_from_reasoning_thinking():
    state = State(query="test query")
    reasoning_result = {"thinking": "This is my reasoning process..."}

    update_from_reasoning(state, reasoning_result)

    assert len(state.workspace.thoughts) == 1
    assert state.workspace.thoughts[0]["reasoning"] == "This is my reasoning process..."


def test_update_from_reasoning_combined():
    state = State(query="test query")
    reasoning_result = {
        "response": "Combined response",
        "actions": ["combined_action"],
        "thinking": "Combined thinking",
    }

    update_from_reasoning(state, reasoning_result)

    assert state.execution.response == "Combined response"
    assert state.execution.pending_calls == ["combined_action"]
    assert len(state.workspace.thoughts) == 1
    assert state.workspace.thoughts[0]["reasoning"] == "Combined thinking"


def test_update_from_reasoning_empty():
    state = State(query="test query")
    reasoning_result = {}

    update_from_reasoning(state, reasoning_result)

    assert state.execution.response is None
    assert len(state.execution.pending_calls) == 0
    assert len(state.workspace.thoughts) == 0


def test_update_from_reasoning_partial():
    state = State(query="test query")
    reasoning_result = {"response": "Only response"}

    update_from_reasoning(state, reasoning_result)

    assert state.execution.response == "Only response"
    assert len(state.execution.pending_calls) == 0


def test_update_from_reasoning_overwrites():
    state = State(query="test query")
    state.execution.pending_calls = ["old_action"]

    reasoning_result = {"actions": ["new_action1", "new_action2"]}

    update_from_reasoning(state, reasoning_result)

    assert state.execution.pending_calls == ["new_action1", "new_action2"]


def test_conversation_execution_sync():
    state = State(query="test query")

    add_message(state, "user", "First user message")
    add_message(state, "assistant", "First assistant response")

    assert len(state.conversation.messages) == len(state.execution.messages)

    for conv_msg, exec_msg in zip(state.conversation.messages, state.execution.messages):
        assert conv_msg["role"] == exec_msg["role"]
        assert conv_msg["content"] == exec_msg["content"]


def test_reasoning_workspace_integration():
    state = State(query="test query")

    reasoning_result = {
        "thinking": "I need to analyze this problem step by step",
        "response": "Based on my analysis, the answer is 42",
    }

    update_from_reasoning(state, reasoning_result)

    assert len(state.workspace.thoughts) > 0
    assert state.execution.response == "Based on my analysis, the answer is 42"

    assert isinstance(state.last_updated, datetime)
