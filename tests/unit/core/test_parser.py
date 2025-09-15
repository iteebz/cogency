"""Parser destruction tests - malformed inputs and edge cases."""

import pytest

from cogency.core.parser import parse_tokens


async def mock_token_stream(tokens):
    """Mock token stream for testing."""
    for token in tokens:
        yield token


@pytest.mark.asyncio
async def test_basic_protocol():
    """Basic protocol flow - state transitions work."""
    tokens = ["Hello", " §think:", " analyzing", " §respond:", " done"]

    events = []
    async for event in parse_tokens(mock_token_stream(tokens)):
        events.append(event)

    assert len(events) == 3
    assert events[0] == {"type": "respond", "content": "Hello"}
    assert events[1] == {"type": "think", "content": " analyzing"}
    assert events[2] == {"type": "respond", "content": " done"}


@pytest.mark.asyncio
async def test_split_delimiter_across_tokens():
    """CRITICAL: Delimiter split across tokens should parse correctly."""
    # Reproduces exact Gemini case: '§think' + ': content'
    tokens = ["§think", ": The user is asking to read 'test.txt'", " §end"]

    events = []
    async for event in parse_tokens(mock_token_stream(tokens)):
        events.append(event)

    # Should get: think event + end event
    assert len(events) == 2, f"Expected 2 events, got {len(events)}: {events}"
    assert events[0]["type"] == "think"
    assert events[0]["content"] == "The user is asking to read 'test.txt'"
    assert events[1]["type"] == "end"


@pytest.mark.asyncio
async def test_end_delimiter_terminates():
    """Test END delimiter emits event and terminates stream."""
    tokens = ["Done", " with", " task", " §end:", " ignored", " content"]

    events = []
    async for event in parse_tokens(mock_token_stream(tokens)):
        events.append(event)

    # Should terminate at END, ignoring remaining tokens
    assert len(events) == 4
    assert events[0]["content"] == "Done"
    assert events[1]["content"] == " with"
    assert events[2]["content"] == " task"
    assert events[3]["type"] == "end"
    # Stream terminated - "ignored content" not processed


@pytest.mark.asyncio
async def test_malformed_delimiters():
    """Destruction test: Malformed delimiters treated as regular content."""
    tokens = ["§invalid:", " §", " BROKEN:", " §think", " without", " colon"]

    events = []
    async for event in parse_tokens(mock_token_stream(tokens)):
        events.append(event)

    # Malformed delimiters treated as regular content, §think requires colon now
    assert len(events) == 4
    assert events[0]["content"] == "§invalid:"  # Invalid delimiter as content
    assert events[1]["content"] == "§BROKEN:"  # Combined malformed delimiter as content
    # "§think without colon" treated as separate tokens
    assert events[2]["content"] == "§thinkwithout"
    assert events[3]["content"] == " colon"


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
    assert events[1]["content"] == " normal"


@pytest.mark.asyncio
async def test_delimiter_boundary_splitting():
    """Destruction test: Delimiter split across multiple tokens."""
    # Split "§think:" across multiple tokens
    tokens = ["§thi", "NK:", " content"]

    events = []
    async for event in parse_tokens(mock_token_stream(tokens)):
        events.append(event)

    assert len(events) == 1
    assert events[0]["type"] == "think"
    assert events[0]["content"] == " content"


@pytest.mark.asyncio
async def test_multi_token_delimiter():
    """Delimiter split across multiple tokens with content."""
    # OpenAI streams: ["§", "respond", ":", " The", " answer", " §", "end"]
    tokens = ["§", "respond", ":", " The", " answer", " §", "end"]

    events = []
    async for event in parse_tokens(mock_token_stream(tokens)):
        events.append(event)

    assert len(events) == 3
    assert events[0] == {"type": "respond", "content": " The"}
    assert events[1] == {"type": "respond", "content": " answer"}
    assert events[2] == {"type": "end"}


@pytest.mark.asyncio
async def test_single_token_delimiter():
    """Single-token delimiter with embedded content."""
    tokens = ["§think: analyzing", " §execute", " §end"]

    events = []
    async for event in parse_tokens(mock_token_stream(tokens)):
        events.append(event)

    assert len(events) == 3
    assert events[0] == {"type": "think", "content": "analyzing"}
    assert events[1] == {"type": "execute"}
    assert events[2] == {"type": "end"}


@pytest.mark.asyncio
async def test_embedded_delimiter():
    """Content token with embedded delimiter - Gemini pattern."""
    tokens = ["§respond: The answer is 8\n§end"]

    events = []
    async for event in parse_tokens(mock_token_stream(tokens)):
        events.append(event)

    assert len(events) == 2
    assert events[0] == {"type": "respond", "content": "The answer is 8\n"}
    assert events[1] == {"type": "end"}


@pytest.mark.asyncio
async def test_embedded_delimiter_simple():
    """Simple embedded delimiter without newline."""
    tokens = ["8\n§end"]

    events = []
    async for event in parse_tokens(mock_token_stream(tokens)):
        events.append(event)
    assert len(events) == 2
    assert events[0] == {"type": "respond", "content": "8\n"}
    assert events[1] == {"type": "end"}


@pytest.mark.asyncio
async def test_split_delimiter_boundary():
    """CRITICAL: Partial delimiter at end of token must combine with next token.

    Token pattern: ['§respond: content\n§', 'think: more content\n§call: {...}']
    The § at the end of token 1 must be preserved for combination with token 2.
    """
    # Test the core boundary case: § at end of token + delimiter start in next token
    tokens = [
        "§respond: I will read the content of test.txt for you.\n§",
        "think: To read the content, I should use the file_read tool.",
    ]

    events = []
    async for event in parse_tokens(mock_token_stream(tokens)):
        events.append(event)

    # Should parse both delimiters correctly across token boundary
    assert len(events) == 2, f"Expected 2 events, got {len(events)}: {events}"
    assert events[0]["type"] == "respond"
    assert "I will read the content" in events[0]["content"]
    assert events[1]["type"] == "think"
    assert "To read the content" in events[1]["content"]


@pytest.mark.asyncio
async def test_multiple_embedded_delimiters():
    """CRITICAL: Multiple delimiters within single token (Gemini pattern).

    Gemini sends complex tokens like: 'think: content\n§call: {...}\n§execute'
    All embedded delimiters must be parsed correctly.
    """
    tokens = [
        "§respond: I will read the content of test.txt for you.\n§",
        'think: To read the content, I should use the file_read tool.\n§call: {"name": "file_read", "args": {"file": "test.txt"}}\n§execute',
    ]

    events = []
    async for event in parse_tokens(mock_token_stream(tokens)):
        events.append(event)

    # Should parse all embedded delimiters: respond, think, call, execute
    assert len(events) == 4, f"Expected 4 events, got {len(events)}: {events}"
    assert events[0]["type"] == "respond"
    assert "I will read the content" in events[0]["content"]
    assert events[1]["type"] == "think"
    assert "To read the content" in events[1]["content"]
    assert events[2]["type"] == "call"
    assert "file_read" in events[2]["content"]
    assert events[3]["type"] == "execute"
