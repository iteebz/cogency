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

    # Mock config to prevent tool execution
    class MockConfig:
        tools = []

    accumulator = Accumulator(
        config=MockConfig(), user_id="test", conversation_id="test", chunks=True
    )

    events = []
    async for event in accumulator.process(mock_parser_events()):
        events.append(event)

    # Should get all 6 individual events plus 1 tool result
    assert len(events) == 7  # 6 original + 1 tool result

    # First few events should be individual think tokens
    assert events[0] == {"type": "think", "content": "I need to", "timestamp": 1.0}
    assert events[1] == {"type": "think", "content": " analyze", "timestamp": 1.1}
    assert events[2] == {"type": "think", "content": " this", "timestamp": 1.2}

    # Call event
    assert events[3] == {"type": "call", "content": '{"name": "search"}', "timestamp": 2.0}

    # Response events
    assert events[4] == {"type": "respond", "content": "Found", "timestamp": 3.0}

    # Tool result from call execution
    assert events[5]["type"] == "result"

    # Final response
    assert events[6] == {"type": "respond", "content": " results", "timestamp": 3.1}


@pytest.mark.asyncio
async def test_chunks_false():
    """Test chunks=False - should get accumulated semantic events."""

    # Mock config to prevent tool execution
    class MockConfig:
        tools = []

    accumulator = Accumulator(
        config=MockConfig(), user_id="test", conversation_id="test", chunks=False
    )

    events = []
    async for event in accumulator.process(mock_parser_events()):
        events.append(event)

    # Should get 4 events: think, call, result, respond
    assert len(events) == 4

    # Accumulated think event
    assert events[0]["type"] == "think"
    assert events[0]["content"] == "I need to analyze this"
    assert events[0]["timestamp"] == 1.0

    # Call event (single, no accumulation needed)
    assert events[1]["type"] == "call"
    assert events[1]["content"] == '{"name": "search"}'
    assert events[1]["timestamp"] == 2.0

    # Tool result event
    assert events[2]["type"] == "result"

    # Final response event (content consumed during accumulation)
    assert events[3]["type"] == "respond"


@pytest.mark.asyncio
async def test_direct_persistence():
    """Test that accumulator persists directly to storage."""
    # Mock resilient_save to capture calls
    saved_calls = []

    async def mock_resilient_save(conversation_id, user_id, msg_type, content, timestamp):
        saved_calls.append(
            {
                "conversation_id": conversation_id,
                "user_id": user_id,
                "msg_type": msg_type,
                "content": content,
                "timestamp": timestamp,
            }
        )
        return True

    # Patch resilient_save
    import cogency.lib.resilience

    original_save = cogency.lib.resilience.resilient_save
    cogency.lib.resilience.resilient_save = mock_resilient_save

    try:
        accumulator = Accumulator(
            config=None, user_id="test", conversation_id="test_conv", chunks=True
        )

        # Consume all events
        events = []
        async for event in accumulator.process(mock_parser_events()):
            events.append(event)

        # Should directly persist 3 accumulated semantic events
        assert len(saved_calls) == 3

        # Check accumulated content was persisted correctly
        assert saved_calls[0]["content"] == "I need to analyze this"
        assert saved_calls[0]["msg_type"] == "think"
        assert saved_calls[1]["content"] == '{"name": "search"}'
        assert saved_calls[1]["msg_type"] == "call"
        assert saved_calls[2]["content"] == "Found results"
        assert saved_calls[2]["msg_type"] == "respond"

    finally:
        # Restore original function
        cogency.lib.resilience.resilient_save = original_save
