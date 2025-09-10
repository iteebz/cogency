"""Tests for continuous streaming behavior with Event.END."""

import pytest

from cogency.core.parser import parse_stream
from cogency.core.protocols import Event


@pytest.mark.asyncio
async def test_continuous_respond_events():
    """Test that multiple RESPOND events are processed correctly."""

    async def mock_stream():
        tokens = [
            "Starting task",
            "§RESPOND",
            "Step 1 complete",
            "§RESPOND",
            "Step 2 complete",
            "§RESPOND",
            "All done",
            "§END",
        ]
        for token in tokens:
            yield token

    events = []
    async for event in parse_stream(mock_stream()):
        events.append(event)

    # Should get: think, respond, respond, respond, end
    assert len(events) == 5
    assert events[0]["type"] == Event.THINK
    assert events[1]["type"] == Event.RESPOND
    assert events[2]["type"] == Event.RESPOND
    assert events[3]["type"] == Event.RESPOND
    assert events[4]["type"] == Event.END

    # Check content
    assert events[0]["content"] == "Starting task"
    assert events[1]["content"] == "Step 1 complete"
    assert events[2]["content"] == "Step 2 complete"
    assert events[3]["content"] == "All done"
    assert events[4]["content"] == ""  # END has empty content


@pytest.mark.asyncio
async def test_end_delimiter_properties():
    """Test Event.END delimiter properties."""

    # Test delimiter string
    assert Event.END.delimiter == "§END"

    # Test enum value
    assert Event.END.value == "end"
    assert Event.END == "end"  # String comparison works


@pytest.mark.asyncio
async def test_mixed_event_stream():
    """Test stream with think, calls, respond, and end events."""

    async def mock_stream():
        tokens = [
            "Let me help you",
            "§THINK",
            "I need to call a tool",
            "§CALLS",
            '[{"name": "test", "args": {}}]',
            "§RESPOND",
            "Tool executed, continuing...",
            "§THINK",
            "Now finishing up",
            "§RESPOND",
            "Task complete",
            "§END",
        ]
        for token in tokens:
            yield token

    events = []
    async for event in parse_stream(mock_stream()):
        events.append(event)

    # Should get proper event sequence (first content is THINK by default)
    event_types = [event["type"] for event in events]
    expected = ["think", "think", "calls", "respond", "think", "respond", "end"]
    assert event_types == expected

    # Check CALLS parsing
    calls_event = events[2]
    assert calls_event["type"] == Event.CALLS
    assert "calls" in calls_event
    assert calls_event["calls"][0]["name"] == "test"


@pytest.mark.asyncio
async def test_end_without_respond():
    """Test that END can come directly after other events."""

    async def mock_stream():
        tokens = ["Just thinking", "§THINK", "Done thinking", "§END"]
        for token in tokens:
            yield token

    events = []
    async for event in parse_stream(mock_stream()):
        events.append(event)

    assert len(events) == 3
    assert events[0]["type"] == Event.THINK  # Initial content is think (parser default)
    assert events[1]["type"] == Event.THINK
    assert events[2]["type"] == Event.END


@pytest.mark.asyncio
async def test_parser_handles_all_events():
    """Test parser recognizes all event types including END."""

    from cogency.core.parser import _build_pattern

    pattern = _build_pattern()

    # Test all event delimiters are recognized
    test_cases = ["§THINK", "§CALLS", "§RESPOND", "§YIELD", "§END"]

    for delimiter in test_cases:
        match = pattern.search(delimiter + " content")
        assert match is not None, f"Pattern should match {delimiter}"
        assert (
            match.group(1) == delimiter[1:]
        ), f"Should extract correct event name from {delimiter}"
