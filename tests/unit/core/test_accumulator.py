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
        {"type": "execute", "content": "", "timestamp": 2.1},
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

    # Should get all 7 individual events plus 1 tool result
    assert len(events) == 8  # 7 original + 1 tool result

    # First few events should be individual think tokens
    assert events[0] == {"type": "think", "content": "I need to", "timestamp": 1.0}
    assert events[1] == {"type": "think", "content": " analyze", "timestamp": 1.1}
    assert events[2] == {"type": "think", "content": " this", "timestamp": 1.2}

    # Call event
    assert events[3] == {"type": "call", "content": '{"name": "search"}', "timestamp": 2.0}
    
    # Execute event
    assert events[4] == {"type": "execute", "content": "", "timestamp": 2.1}

    # Response events
    assert events[5] == {"type": "respond", "content": "Found", "timestamp": 3.0}

    # Tool result from call execution
    assert events[6]["type"] == "result"

    # Final response
    assert events[7] == {"type": "respond", "content": " results", "timestamp": 3.1}


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
    assert isinstance(events[0]["timestamp"], float)

    # Call event (single, no accumulation needed)
    assert events[1]["type"] == "call"
    assert events[1]["content"] == '{"name": "search", "args": {}}'
    assert isinstance(events[1]["timestamp"], float)

    # Tool result event (should exist even when tool fails)
    assert events[2]["type"] == "result"

    # Final response event (content consumed during accumulation)
    assert events[3]["type"] == "respond"


@pytest.mark.asyncio
async def test_direct_persistence():
    """Test that accumulator persists directly to storage."""
    from unittest.mock import AsyncMock, patch

    saved_calls = []

    async def track_calls(*args, **kwargs):
        saved_calls.append(
            {
                "conversation_id": args[0],
                "user_id": args[1],
                "msg_type": args[2],
                "content": args[3],
                "timestamp": kwargs.get("timestamp"),
            }
        )

    with patch("cogency.core.accumulator.save_message", new_callable=AsyncMock) as mock_save:
        mock_save.side_effect = track_calls

        accumulator = Accumulator(
            config=None, user_id="test", conversation_id="test_conv", chunks=True
        )

        # Consume all events
        events = []
        async for event in accumulator.process(mock_parser_events()):
            events.append(event)

        # Should persist 4 messages: think, call, result, respond
        assert len(saved_calls) == 4

        # Check accumulated content was persisted correctly
        assert saved_calls[0]["content"] == "I need to analyze this"
        assert saved_calls[0]["msg_type"] == "think"
        assert saved_calls[1]["content"] == '{"name": "search", "args": {}}'
        assert saved_calls[1]["msg_type"] == "call"
        # Tool execution result (failure since no config.tools)
        assert saved_calls[2]["msg_type"] == "result"
        assert (
            "Tool execution failed" in saved_calls[2]["content"]
            or "not found" in saved_calls[2]["content"]
        )
        assert saved_calls[3]["content"] == "Found results"
        assert saved_calls[3]["msg_type"] == "respond"


@pytest.mark.asyncio
async def test_double_execute_delimiter_cleaning():
    """Test accumulator correctly handles double §EXECUTE delimiters from LLM."""
    import json
    from unittest.mock import AsyncMock, MagicMock
    
    config = MagicMock()
    config.tools = []
    
    accumulator = Accumulator(config, "test_user", "test_conv", chunks=False)
    accumulator._execute_tool = AsyncMock(return_value={
        "type": "result", 
        "outcome": "Test completed", 
        "content": "Test result",
        "timestamp": 123.0
    })
    
    # Simulate parser events with contaminated call content  
    parser_events = [
        {"type": "call", "content": '{"name": "test", "args": {}}', "timestamp": 101.0},
        {"type": "call", "content": " §EXECUTE§EXECUTE", "timestamp": 102.0},  # Double execute
        {"type": "execute", "content": "", "timestamp": 103.0},
    ]
    
    async def mock_parser():
        for event in parser_events:
            yield event
    
    events = []
    async for event in accumulator.process(mock_parser()):
        events.append(event)
    
    # Should get clean events without §EXECUTE contamination
    call_events = [e for e in events if e["type"] == "call"]
    assert len(call_events) == 1
    
    # Call content should be clean JSON without §EXECUTE
    call_content = call_events[0]["content"]
    parsed_call = json.loads(call_content)
    assert parsed_call == {"name": "test", "args": {}}
    assert "§EXECUTE" not in call_content
