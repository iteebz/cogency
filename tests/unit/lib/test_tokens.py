import pytest

from cogency.lib.tokens import Tokens, count_message_tokens, count_tokens


def test_token_counting_behavior():
    """Token counting with model support and fallbacks."""

    # Token counting behavior
    assert count_tokens("Hello world", "gpt-4o") > 0
    assert count_tokens("", "gpt-4o") == 0
    assert count_tokens("test", "unknown-model") >= 0  # Fallback approximation

    # Tokens class tracking
    tracker = Tokens("gpt-4o")

    input_tokens = tracker.add_input("Hello world")
    output_tokens = tracker.add_output("Hi there")

    assert tracker.input == input_tokens > 0
    assert tracker.output == output_tokens > 0
    assert tracker.total() == input_tokens + output_tokens

    # Model validation
    with pytest.raises(ValueError, match="Model must be specified explicitly"):
        Tokens("")

    # Metrics event generation
    tracker.input = 1000
    tracker.output = 500
    metrics = tracker.to_metrics_event(duration=1.5)

    assert metrics["type"] == "metrics"
    assert metrics["input_tokens"] == 1000
    assert metrics["output_tokens"] == 500
    assert metrics["duration"] == 1.5


def test_message_token_counting():
    """Test tiktoken native message encoding and fallbacks."""
    messages = [
        {"role": "system", "content": "You are a helpful assistant"},
        {"role": "user", "content": "Hello world"},
    ]

    # OpenAI models use native tiktoken encoding
    gpt_tokens = count_message_tokens(messages, "gpt-4o")
    assert gpt_tokens > 0

    # Non-OpenAI models use concatenation fallback
    claude_tokens = count_message_tokens(messages, "claude-sonnet-4")
    assert claude_tokens > 0

    # Empty messages
    assert count_message_tokens([], "gpt-4o") == 0
    assert count_message_tokens(None, "gpt-4o") == 0


def test_add_input_messages():
    """Test Tokens.add_input_messages() method."""
    tracker = Tokens("gpt-4o")

    messages = [
        {"role": "system", "content": "System prompt"},
        {"role": "user", "content": "User query"},
    ]

    # Add input tokens from messages
    tokens = tracker.add_input_messages(messages)
    assert tracker.input == tokens > 0
    assert tracker.output == 0  # No output yet

    # Add output tokens
    output_tokens = tracker.add_output("Response text")
    assert tracker.output == output_tokens > 0
    assert tracker.total() == tokens + output_tokens

    # Empty messages should add 0 tokens
    initial_input = tracker.input
    tracker.add_input_messages([])
    assert tracker.input == initial_input
