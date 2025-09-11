"""Unit tests for Accumulator - chunks=True vs chunks=False behavior."""

import pytest

from cogency.core.accumulator import Accumulator


async def mock_parser_events():
    """Mock parser events for testing."""
    events = [
        {"type": "think", "content": "I need to", "timestamp": 1.0},
        {"type": "think", "content": " analyze", "timestamp": 1.1},
        {"type": "think", "content": " this", "timestamp": 1.2},
        {"type": "call", "content": '{"name": "search"}', "timestamp": 2.0},
        {"type": "respond", "content": "Found", "timestamp": 3.0},
        {"type": "respond", "content": " results", "timestamp": 3.1},
    ]
    
    for event in events:
        yield event


@pytest.mark.asyncio
async def test_chunks_true():
    """Test chunks=True - should get individual parser events."""
    accumulator = Accumulator(chunks=True)
    
    events = []
    async for event in accumulator.process(mock_parser_events()):
        events.append(event)
    
    # Should get all 6 individual events
    assert len(events) == 6
    
    # First few events should be individual think tokens
    assert events[0] == {"type": "think", "content": "I need to", "timestamp": 1.0}
    assert events[1] == {"type": "think", "content": " analyze", "timestamp": 1.1}
    assert events[2] == {"type": "think", "content": " this", "timestamp": 1.2}
    
    # Call event
    assert events[3] == {"type": "call", "content": '{"name": "search"}', "timestamp": 2.0}
    
    # Response events
    assert events[4] == {"type": "respond", "content": "Found", "timestamp": 3.0}
    assert events[5] == {"type": "respond", "content": " results", "timestamp": 3.1}


@pytest.mark.asyncio
async def test_chunks_false():
    """Test chunks=False - should get accumulated semantic events."""
    accumulator = Accumulator(chunks=False)
    
    events = []
    async for event in accumulator.process(mock_parser_events()):
        events.append(event)
    
    # Should get 3 accumulated events (think, call, respond)
    assert len(events) == 3
    
    # Accumulated think event
    assert events[0]["type"] == "think"
    assert events[0]["content"] == "I need to analyze this"
    assert events[0]["timestamp"] == 1.0
    
    # Call event (single, no accumulation needed)
    assert events[1]["type"] == "call"
    assert events[1]["content"] == '{"name": "search"}'
    assert events[1]["timestamp"] == 2.0
    
    # Accumulated response event
    assert events[2]["type"] == "respond"
    assert events[2]["content"] == "Found results"
    assert events[2]["timestamp"] == 3.0


@pytest.mark.asyncio
async def test_persistence_callback():
    """Test that persistence callback is called for accumulated events."""
    persisted_events = []
    
    def mock_persist(event):
        persisted_events.append(event)
    
    accumulator = Accumulator(chunks=True, on_persist=mock_persist)
    
    # Consume all events
    events = []
    async for event in accumulator.process(mock_parser_events()):
        events.append(event)
    
    # Should persist 3 accumulated semantic events regardless of chunks=True
    assert len(persisted_events) == 3
    
    # Check accumulated content was persisted correctly
    assert persisted_events[0]["content"] == "I need to analyze this"
    assert persisted_events[1]["content"] == '{"name": "search"}'
    assert persisted_events[2]["content"] == "Found results"