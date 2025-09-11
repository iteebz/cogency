"""Stream processing tests."""

import pytest

from cogency.core.parser import parse_stream
from cogency.core.protocols import Event


async def mock_stream(tokens):
    """Simple mock stream."""
    for token in tokens:
        yield token


@pytest.mark.asyncio
async def test_stream_processing():
    """Parser processes token streams into proper event sequences."""

    # Basic stream processing
    tokens = ["§THINK", "reasoning", "§RESPOND", "answer", "§EXECUTE"]
    events = [e async for e in parse_stream(mock_stream(tokens))]

    event_types = [e["type"] for e in events]
    assert "think" in event_types
    assert "respond" in event_types
    assert "execute" in event_types

    # Tool call processing
    call_tokens = ["§CALLS", '[{"name": "test", "args": {}}]', "§EXECUTE"]
    events = [e async for e in parse_stream(mock_stream(call_tokens))]

    calls_events = [e for e in events if e["type"] == Event.CALLS]
    assert len(calls_events) == 1
    assert calls_events[0]["calls"][0]["name"] == "test"

    # Multiple response processing
    multi_tokens = ["§RESPOND", "step1", "§RESPOND", "step2", "§END"]
    events = [e async for e in parse_stream(mock_stream(multi_tokens))]

    respond_events = [e for e in events if e["type"] == Event.RESPOND]
    assert len(respond_events) == 2
    assert respond_events[0]["content"] == "step1"
    assert respond_events[1]["content"] == "step2"

    # Chunked delimiter handling
    chunked = ["§", "TH", "INK", " content", "§", "RESP", "OND", " answer"]
    events = [e async for e in parse_stream(mock_stream(chunked))]

    think_events = [e for e in events if e["type"] == Event.THINK]
    respond_events = [e for e in events if e["type"] == Event.RESPOND]
    assert len(think_events) >= 1
    assert len(respond_events) >= 1
