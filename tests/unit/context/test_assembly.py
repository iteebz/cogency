"""Context assembly tests - Simple integration tests."""

from cogency.context import context


def test_basic_assembly():
    """Context assembly returns system + user messages."""
    messages = context.assemble("Test query", "user_123", "conv_123", config=None)

    assert len(messages) >= 2
    assert messages[0]["role"] == "system"
    assert messages[-1]["role"] == "user"
    assert messages[-1]["content"] == "Test query"


def test_user_message_content():
    """User message contains the exact query."""
    query = "What is 2+2?"
    messages = context.assemble(query, "user_123", "conv_123", config=None)

    user_message = messages[-1]
    assert user_message["role"] == "user"
    assert user_message["content"] == query


def test_system_message_exists():
    """System message is generated and contains instructions."""
    messages = context.assemble("Test", "user_123", "conv_123", config=None)

    system_message = messages[0]
    assert system_message["role"] == "system"
    assert isinstance(system_message["content"], str)
    assert len(system_message["content"]) > 0
