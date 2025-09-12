"""Unit tests for stream observation and metrics collection."""

import pytest

from cogency.lib.observe import Observer, observe


async def mock_stream_events():
    """Mock stream for testing."""
    events = [
        {"type": "think", "content": "analyzing", "timestamp": 1.0},
        {"type": "respond", "content": "result", "timestamp": 2.0},
        {"type": "end", "content": "", "timestamp": 3.0},
    ]
    for event in events:
        yield event


@pytest.mark.asyncio
async def test_observer_input_and_output_tracking():
    """Test Observer tracks both input and output tokens."""
    input_messages = [
        {"role": "system", "content": "You are helpful"},
        {"role": "user", "content": "Hello world"},
    ]

    observer = Observer(mock_stream_events(), "gpt-4o", input_messages=input_messages)

    # Consume stream
    events = []
    async for event in observer:
        events.append(event)

    # Verify stream passthrough
    assert len(events) == 3
    assert events[0]["content"] == "analyzing"
    assert events[1]["content"] == "result"

    # Verify token tracking
    metrics = observer.get_metrics()
    assert metrics["input_tokens"] > 0  # From input_messages
    assert metrics["output_tokens"] > 0  # From stream content
    assert metrics["duration"] > 0


@pytest.mark.asyncio
async def test_observer_without_input_messages():
    """Test Observer works without input messages."""
    observer = Observer(mock_stream_events(), "gpt-4o")

    # Consume stream
    events = []
    async for event in observer:
        events.append(event)

    metrics = observer.get_metrics()
    assert metrics["input_tokens"] == 0  # No input messages provided
    assert metrics["output_tokens"] > 0  # From stream content
    assert metrics["duration"] > 0


@pytest.mark.asyncio
async def test_observer_empty_content_handling():
    """Test Observer handles empty content gracefully."""

    async def empty_stream():
        yield {"type": "end", "content": "", "timestamp": 1.0}
        yield {"type": "respond", "timestamp": 2.0}  # No content field

    observer = Observer(empty_stream(), "gpt-4o")

    events = []
    async for event in observer:
        events.append(event)

    metrics = observer.get_metrics()
    assert metrics["output_tokens"] == 0  # No trackable content
    assert metrics["duration"] > 0


@pytest.mark.asyncio
async def test_observe_decorator():
    """Test @observe decorator functionality."""

    class MockAgent:
        def __init__(self):
            self.config = type("Config", (), {"llm": type("LLM", (), {"llm_model": "gpt-4o"})})()

    agent = MockAgent()

    @observe(agent)
    async def test_stream():
        async for event in mock_stream_events():
            yield event

    # Consume decorated stream
    events = []
    stream_instance = test_stream()
    async for event in stream_instance:
        events.append(event)

    # Verify decorator attached metrics
    assert hasattr(test_stream, "metrics")
    metrics = test_stream.metrics
    assert metrics["input_tokens"] == 0  # Decorator doesn't track input
    assert metrics["output_tokens"] > 0  # Tracks output from stream
    assert metrics["duration"] > 0
