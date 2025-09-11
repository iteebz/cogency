"""Unit tests for pure Parser - just sticky note state + token emission."""

import pytest

from cogency.core.parser import parse_tokens


async def mock_token_stream(tokens):
    """Mock token stream for testing."""
    for token in tokens:
        yield token


@pytest.mark.asyncio
async def test_pure_token_emission():
    """Test parser emits individual tokens with sticky note state."""
    tokens = ["Hello", " world", "!"]
    
    events = []
    async for event in parse_tokens(mock_token_stream(tokens)):
        events.append(event)
    
    # Should emit 3 individual token events
    assert len(events) == 3
    assert events[0]["type"] == "respond"  # Default state
    assert events[0]["content"] == "Hello"
    assert events[1]["type"] == "respond"
    assert events[1]["content"] == " world"
    assert events[2]["type"] == "respond" 
    assert events[2]["content"] == "!"


@pytest.mark.asyncio
async def test_delimiter_detection_and_state_change():
    """Test delimiter detection changes sticky note state."""
    tokens = ["Thinking", "§THINK:", " about", " this"]
    
    events = []
    async for event in parse_tokens(mock_token_stream(tokens)):
        events.append(event)
    
    # Should get content before delimiter + new state for remaining tokens
    assert len(events) == 3
    
    # Content before delimiter with old state
    assert events[0]["type"] == "respond"  # Default state
    assert events[0]["content"] == "Thinking"
    
    # Content after delimiter with new state  
    assert events[1]["type"] == "think"
    assert events[1]["content"] == " about"
    assert events[2]["type"] == "think" 
    assert events[2]["content"] == " this"


@pytest.mark.asyncio
async def test_execute_delimiter():
    """Test EXECUTE delimiter emits special event."""
    tokens = ["Call tool", "§EXECUTE"]
    
    events = []
    async for event in parse_tokens(mock_token_stream(tokens)):
        events.append(event)
    
    assert len(events) == 2
    
    # Content before delimiter
    assert events[0]["type"] == "respond"
    assert events[0]["content"] == "Call tool"
    
    # EXECUTE delimiter event
    assert events[1]["type"] == "execute"
    assert events[1]["content"] == ""


@pytest.mark.asyncio
async def test_end_delimiter_terminates():
    """Test END delimiter emits event and terminates stream."""
    tokens = ["Done with task", "§END", " ignored content"]
    
    events = []
    async for event in parse_tokens(mock_token_stream(tokens)):
        events.append(event)
    
    # Should only get 2 events - content + END, then terminate
    assert len(events) == 2
    
    assert events[0]["type"] == "respond"
    assert events[0]["content"] == "Done with task"
    
    assert events[1]["type"] == "end"
    assert events[1]["content"] == ""
    # Stream should terminate, ignored content not processed


@pytest.mark.asyncio
async def test_multiple_state_transitions():
    """Test multiple delimiter state transitions work correctly.""" 
    tokens = ["Start", "§THINK:", "analyzing", "§CALL:", "search", "§RESPOND:", "found results"]
    
    events = []
    async for event in parse_tokens(mock_token_stream(tokens)):
        events.append(event)
    
    assert len(events) == 4
    
    # Start with default respond state
    assert events[0]["type"] == "respond"
    assert events[0]["content"] == "Start"
    
    # Think state 
    assert events[1]["type"] == "think"
    assert events[1]["content"] == "analyzing"
    
    # Call state
    assert events[2]["type"] == "call"
    assert events[2]["content"] == "search"
    
    # Back to respond state
    assert events[3]["type"] == "respond"
    assert events[3]["content"] == "found results"


@pytest.mark.asyncio
async def test_delimiter_within_token():
    """Test delimiter detection within a single token."""
    tokens = ["Hello§THINK:world"]
    
    events = []
    async for event in parse_tokens(mock_token_stream(tokens)):
        events.append(event)
    
    assert len(events) == 2
    
    # Content before delimiter
    assert events[0]["type"] == "respond"
    assert events[0]["content"] == "Hello"
    
    # Content after delimiter with new state
    assert events[1]["type"] == "think" 
    assert events[1]["content"] == "world"


@pytest.mark.asyncio
async def test_empty_content_handling():
    """Test parser handles empty content gracefully."""
    tokens = ["", "§THINK:", "", "content"]
    
    events = []
    async for event in parse_tokens(mock_token_stream(tokens)):
        events.append(event)
    
    # Should only emit non-empty content
    assert len(events) == 1
    assert events[0]["type"] == "think"
    assert events[0]["content"] == "content"