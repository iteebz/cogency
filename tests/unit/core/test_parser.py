"""Unit tests for word-bounded Parser with destruction testing."""

import pytest

from cogency.core.parser import parse_tokens


async def mock_token_stream(tokens):
    """Mock token stream for testing."""
    for token in tokens:
        yield token


@pytest.mark.asyncio
async def test_word_emission_basic():
    """Test parser emits words on whitespace boundaries."""
    tokens = ["Hello", " world", " test"]

    events = []
    async for event in parse_tokens(mock_token_stream(tokens)):
        events.append(event)

    # Should emit 3 words
    assert len(events) == 3
    assert events[0]["type"] == "respond"
    assert events[0]["content"] == "Hello"
    assert events[1]["type"] == "respond"
    assert events[1]["content"] == "world"
    assert events[2]["type"] == "respond"
    assert events[2]["content"] == "test"


@pytest.mark.asyncio
async def test_delimiter_state_transition():
    """Test delimiter detection changes state for subsequent words."""
    tokens = ["Hello", " ", "§THINK:", " analyzing", " data"]

    events = []
    async for event in parse_tokens(mock_token_stream(tokens)):
        events.append(event)

    assert len(events) == 3
    # Content before delimiter
    assert events[0]["type"] == "respond"
    assert events[0]["content"] == "Hello"
    # Content after delimiter with new state
    assert events[1]["type"] == "think"
    assert events[1]["content"] == "analyzing"
    assert events[2]["type"] == "think"
    assert events[2]["content"] == "data"


@pytest.mark.asyncio
async def test_execute_delimiter_emission():
    """Test EXECUTE delimiter emits event and continues."""
    tokens = ["Tool", " call", " §EXECUTE", " more", " content"]

    events = []
    async for event in parse_tokens(mock_token_stream(tokens)):
        events.append(event)

    assert len(events) == 5
    assert events[0]["content"] == "Tool"
    assert events[1]["content"] == "call"
    # EXECUTE delimiter
    assert events[2]["type"] == "execute"
    assert events[2]["content"] == ""
    # Continues after EXECUTE
    assert events[3]["content"] == "more"
    assert events[4]["content"] == "content"


@pytest.mark.asyncio
async def test_end_delimiter_terminates():
    """Test END delimiter emits event and terminates stream."""
    tokens = ["Done", " with", " task", " §END:", " ignored", " content"]

    events = []
    async for event in parse_tokens(mock_token_stream(tokens)):
        events.append(event)

    # Should terminate at END, ignoring remaining tokens
    assert len(events) == 4
    assert events[0]["content"] == "Done"
    assert events[1]["content"] == "with"
    assert events[2]["content"] == "task"
    assert events[3]["type"] == "end"
    assert events[3]["content"] == ""
    # Stream terminated - "ignored content" not processed


@pytest.mark.asyncio
async def test_multiple_state_transitions():
    """Test complex state transitions work correctly."""
    tokens = [
        "Start",
        " §THINK:",
        " analyzing",
        " §CALL:",
        " search",
        " §RESPOND:",
        " found",
        " results",
    ]

    events = []
    async for event in parse_tokens(mock_token_stream(tokens)):
        events.append(event)

    assert len(events) == 5

    # Start in respond state
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
    assert events[3]["content"] == "found"
    assert events[4]["type"] == "respond"
    assert events[4]["content"] == "results"


@pytest.mark.asyncio
async def test_character_streaming_to_words():
    """Test character-by-character input produces correct word events."""
    # Simulate OpenAI character streaming: "Hello §THINK: world"
    tokens = list("Hello §THINK: world")

    events = []
    async for event in parse_tokens(mock_token_stream(tokens)):
        events.append(event)

    # Should emit words despite character input
    assert len(events) == 2
    assert events[0]["type"] == "respond"
    assert events[0]["content"] == "Hello"
    assert events[1]["type"] == "think"
    assert events[1]["content"] == "world"


@pytest.mark.asyncio
async def test_delimiter_with_content():
    """Test delimiters with trailing content (e.g., §CALL: {data})."""
    tokens = ["§CALL:", ' {"name":', ' "test"}', " §EXECUTE"]

    events = []
    async for event in parse_tokens(mock_token_stream(tokens)):
        events.append(event)

    assert len(events) == 3
    # State transition to call, then content in call state
    assert events[0]["type"] == "call"
    assert events[0]["content"] == '{"name":'
    assert events[1]["type"] == "call"
    assert events[1]["content"] == '"test"}'
    # EXECUTE delimiter
    assert events[2]["type"] == "execute"
    assert events[2]["content"] == ""


# DESTRUCTION TESTING - Edge Cases and Malformed Input


@pytest.mark.asyncio
async def test_empty_tokens():
    """Destruction test: Empty tokens should be handled gracefully."""
    tokens = ["", "Hello", "", " ", "", "world", ""]

    events = []
    async for event in parse_tokens(mock_token_stream(tokens)):
        events.append(event)

    assert len(events) == 2
    assert events[0]["content"] == "Hello"
    assert events[1]["content"] == "world"


@pytest.mark.asyncio
async def test_only_whitespace():
    """Destruction test: Only whitespace should emit nothing."""
    tokens = [" ", "\t", "\n", "   "]

    events = []
    async for event in parse_tokens(mock_token_stream(tokens)):
        events.append(event)

    assert len(events) == 0


@pytest.mark.asyncio
async def test_malformed_delimiters():
    """Destruction test: Malformed delimiters treated as regular content."""
    tokens = ["§INVALID:", " §", " BROKEN:", " §THINK", " without", " colon"]

    events = []
    async for event in parse_tokens(mock_token_stream(tokens)):
        events.append(event)

    # Malformed delimiters treated as regular content, but §THINK without colon actually works
    assert len(events) == 5
    assert events[0]["content"] == "§INVALID:"
    assert events[1]["content"] == "§"
    assert events[2]["content"] == "BROKEN:"
    # "§THINK" without colon is actually valid and transitions state
    assert events[3]["type"] == "think"
    assert events[4]["type"] == "think"


@pytest.mark.asyncio
async def test_non_string_tokens_error():
    """Destruction test: Non-string tokens should raise error."""

    async def bad_token_stream():
        yield "valid"
        yield 123  # Invalid non-string token
        yield "more"

    with pytest.raises(RuntimeError, match="Parser expects string tokens"):
        async for _event in parse_tokens(bad_token_stream()):
            pass


@pytest.mark.asyncio
async def test_massive_word_buffer():
    """Destruction test: Huge words without whitespace."""
    # 10KB word without spaces
    giant_word = "x" * 10000
    tokens = [giant_word, " normal"]

    events = []
    async for event in parse_tokens(mock_token_stream(tokens)):
        events.append(event)

    assert len(events) == 2
    assert events[0]["content"] == giant_word
    assert events[1]["content"] == "normal"


@pytest.mark.asyncio
async def test_rapid_state_changes():
    """Destruction test: Rapid delimiter state changes."""
    tokens = ["§THINK:", " §RESPOND:", " §CALL:", " §THINK:", " content"]

    events = []
    async for event in parse_tokens(mock_token_stream(tokens)):
        events.append(event)

    # Should handle rapid transitions and emit content in final state
    assert len(events) == 1
    assert events[0]["type"] == "think"
    assert events[0]["content"] == "content"


@pytest.mark.asyncio
async def test_delimiter_boundary_splitting():
    """Destruction test: Delimiter split across multiple tokens."""
    # Split "§THINK:" across multiple tokens
    tokens = ["§THI", "NK:", " content"]

    events = []
    async for event in parse_tokens(mock_token_stream(tokens)):
        events.append(event)

    assert len(events) == 1
    assert events[0]["type"] == "think"
    assert events[0]["content"] == "content"


@pytest.mark.asyncio
async def test_compact_delimiter_with_content():
    """Parser splits delimiter from content when LLM omits space after colon."""
    # LLM emits: §CALL:{"name":"test"} instead of §CALL: {"name":"test"}
    tokens = ['§CALL:{"name":"test"}', " more", " content"]

    events = []
    async for event in parse_tokens(mock_token_stream(tokens)):
        events.append(event)

    # Should transition to CALL state and emit JSON as first content
    assert len(events) == 3
    assert events[0]["type"] == "call"
    assert events[0]["content"] == '{"name":"test"}'
    assert events[1]["type"] == "call"
    assert events[1]["content"] == "more"
    assert events[2]["type"] == "call"
    assert events[2]["content"] == "content"
