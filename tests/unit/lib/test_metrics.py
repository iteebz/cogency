"""Test stream-native metrics implementation."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from cogency.core.replay import stream as replay_stream
from cogency.core.resume import stream as resume_stream
from cogency.lib.metrics import Tokens, count_message_tokens, count_tokens


@pytest.mark.asyncio
async def test_replay_metrics_emission():
    """Test that replay mode emits metrics events correctly."""
    # Mock config and LLM
    config = MagicMock()
    config.llm = MagicMock()
    config.llm.llm_model = "gpt-4"
    config.llm.stream = AsyncMock()
    config.max_iterations = 3

    # Mock token stream that ends with §END
    mock_tokens = ["§RESPOND: Hello world", "§END"]
    config.llm.stream.return_value = mock_async_iter(mock_tokens)

    # Mock context assembly
    from cogency.context import context
    context.assemble = AsyncMock(return_value=[{"role": "user", "content": "test"}])

    events = []
    async for event in replay_stream(config, "test", "user", "conv"):
        events.append(event)

    # Should have metrics events
    metrics_events = [e for e in events if e["type"] == "metrics"]
    assert len(metrics_events) > 0

    # Check metrics structure
    metrics = metrics_events[0]
    assert "step" in metrics
    assert "total" in metrics
    assert "input" in metrics["step"]
    assert "output" in metrics["step"]
    assert "duration" in metrics["step"]


@pytest.mark.asyncio
async def test_resume_metrics_emission():
    """Test that resume mode emits metrics events correctly."""
    # Mock config and LLM with WebSocket support
    config = MagicMock()
    config.llm = MagicMock()
    config.llm.llm_model = "gpt-4"
    config.llm.connect = AsyncMock()
    config.llm.receive = AsyncMock()
    config.llm.close = AsyncMock()

    # Mock WebSocket session
    session = MagicMock()
    config.llm.connect.return_value = session

    # Mock token stream
    mock_tokens = ["§RESPOND: Hello world", "§END"]
    config.llm.receive.return_value = mock_async_iter(mock_tokens)

    # Mock context assembly
    from cogency.context import context
    context.assemble = AsyncMock(return_value=[{"role": "user", "content": "test"}])

    events = []
    async for event in resume_stream(config, "test", "user", "conv"):
        events.append(event)

    # Should have metrics events
    metrics_events = [e for e in events if e["type"] == "metrics"]
    assert len(metrics_events) > 0


def test_tokens_step_metrics():
    """Test Tokens.to_step_metrics() method."""
    tokens = Tokens("gpt-4")
    tokens.add_input("test input")
    tokens.add_output("test output")

    metrics = tokens.to_step_metrics(10, 20, 1.5, 5.0)

    assert metrics["type"] == "metrics"
    assert metrics["step"]["input"] == 10
    assert metrics["step"]["output"] == 20
    assert metrics["step"]["duration"] == 1.5
    assert metrics["total"]["input"] == tokens.input
    assert metrics["total"]["output"] == tokens.output
    assert metrics["total"]["duration"] == 5.0


async def mock_async_iter(items):
    """Mock async iterator for testing."""
    for item in items:
        yield item


# Token counting tests (merged from test_tokens.py)

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