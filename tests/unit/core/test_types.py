"""Core types tests."""

from cogency.core.types import AgentResult


def test_agent_result():
    """AgentResult creation."""
    result = AgentResult(response="Test response", conversation_id="test_123")

    assert result.response == "Test response"
    assert result.conversation_id == "test_123"


def test_agent_result_str():
    """AgentResult string representation."""
    result = AgentResult("Hello", "conv_456")

    assert str(result) == "Hello"
