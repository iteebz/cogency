"""Context tests - Simple integration tests."""

import pytest

from cogency.context import context
from cogency.context.assembly import Context
from cogency.core.protocols import Event


def test_imports():
    """Context imports correctly."""
    assert Context is not None
    assert context is not None
    assert isinstance(context, Context)


def test_record_events():
    """Context records batch events."""
    events = [{"type": Event.USER, "content": "Hello", "timestamp": 1234567890.0}]

    # This is integration test - it actually saves to DB
    result = context.record("test_conv", "test_user", events)

    # Should return boolean indicating success
    assert isinstance(result, bool)


def test_assemble_basic():
    """Context assembles basic messages."""
    messages = context.assemble(
        query="Test query", user_id="user_123", conversation_id="conv_123", tools=[], config=None
    )

    assert len(messages) >= 2
    assert messages[0]["role"] == "system"
    assert messages[-1]["role"] == "user"
    assert messages[-1]["content"] == "Test query"


def test_validation():
    """Context validates required parameters."""
    with pytest.raises(ValueError, match="user_id cannot be None"):
        context.assemble(
            query="Test", user_id=None, conversation_id="conv_123", tools=[], config=None
        )
