"""Component tests for parser with realistic token patterns.

Based on empirical testing with real provider output patterns.
Validates parser behavior against actual LLM streaming patterns.
"""

import pytest

from cogency.core.parser import parse_stream


class MockStream:
    """Mock stream that yields tokens like real providers."""

    def __init__(self, tokens):
        self.tokens = tokens

    def __aiter__(self):
        return self

    async def __anext__(self):
        if not self.tokens:
            raise StopAsyncIteration
        return self.tokens.pop(0)


@pytest.mark.asyncio
async def test_parser_with_perfect_delimiter_stream():
    """Test parser with perfect delimiter stream from atomic provider tests."""

    # Token pattern observed from working atomic tests
    perfect_tokens = [
        "§THINK",
        "\n",
        "The user is asking a simple arithmetic question: 2+2.\n",
        "I need to calculate the sum and then present the answer.\n",
        "2 + 2 = 4.",
        "§RESPOND",
        "\n",
        "4",
        "§YIELD",
    ]

    stream = MockStream(perfect_tokens)
    events = []

    async for event in parse_stream(stream):
        events.append(event)

    # Validate event structure
    assert len(events) == 5  # 3 THINK + 1 RESPOND + 1 YIELD

    think_events = [e for e in events if e["type"] == "think"]
    respond_events = [e for e in events if e["type"] == "respond"]
    yield_events = [e for e in events if e["type"] == "yield"]

    assert len(think_events) == 3
    assert len(respond_events) == 1
    assert len(yield_events) == 1

    # Validate content
    assert think_events[0]["content"] == "The user is asking a simple arithmetic question: 2+2."
    assert respond_events[0]["content"] == "4"
    assert yield_events[0]["content"] == "complete"  # YIELD after RESPOND


@pytest.mark.asyncio
async def test_parser_with_chunked_streaming():
    """Test parser with chunked streaming (real provider behavior)."""

    # How providers actually send data - delimiters split across chunks
    chunked_tokens = [
        "§",  # Delimiter starts
        "TH",
        "INK",  # Delimiter completes
        "\n",
        "The user is asking",
        " a simple arithmetic",
        " question: 2+2.\n",
        "2 + 2 = 4.",
        "§",  # Next delimiter starts
        "RESP",
        "OND",  # Delimiter completes
        "\n",
        "4",
        "§",  # Final delimiter
        "YIELD",
    ]

    stream = MockStream(chunked_tokens)
    events = []

    async for event in parse_stream(stream):
        events.append(event)

    # Parser should reassemble delimiters correctly
    think_events = [e for e in events if e["type"] == "think"]
    respond_events = [e for e in events if e["type"] == "respond"]
    yield_events = [e for e in events if e["type"] == "yield"]

    assert len(think_events) == 4  # Multiple chunks create multiple events
    assert len(respond_events) == 1
    assert len(yield_events) == 1

    # Content should be preserved across chunks (parser strips whitespace per chunk)
    total_think_content = "".join(e["content"] for e in think_events)
    # Parser processes each chunk separately and strips whitespace
    expected_chunks = ["The user is asking", "a simple arithmetic", "question: 2+2.", "2 + 2 = 4."]
    for chunk in expected_chunks:
        assert chunk in total_think_content
    assert respond_events[0]["content"] == "4"


@pytest.mark.asyncio
async def test_parser_with_missing_yield():
    """Test parser behavior when YIELD is missing (critical hang scenario)."""

    # Stream ends without YIELD - what causes infinite hangs
    no_yield_tokens = [
        "§THINK",
        "\n",
        "Simple reasoning",
        "§RESPOND",
        "\n",
        "Answer",
        # NO §YIELD - stream just ends
    ]

    stream = MockStream(no_yield_tokens)
    events = []

    async for event in parse_stream(stream):
        events.append(event)

    # Parser should handle gracefully
    think_events = [e for e in events if e["type"] == "think"]
    respond_events = [e for e in events if e["type"] == "respond"]
    yield_events = [e for e in events if e["type"] == "yield"]

    assert len(think_events) == 1
    assert len(respond_events) == 1
    assert len(yield_events) == 0  # No YIELD event generated

    # Content should be preserved
    assert think_events[0]["content"] == "Simple reasoning"
    assert respond_events[0]["content"] == "Answer"


@pytest.mark.asyncio
async def test_parser_with_calls_json():
    """Test parser with realistic function call JSON patterns."""

    # Realistic tool call pattern
    call_tokens = [
        "§THINK",
        "\n",
        "I need to use a tool to help with this request.",
        "§CALLS",
        "\n",
        '[{"name": "search", "args": {"query": "python basics"}}]',
        "§YIELD",
    ]

    stream = MockStream(call_tokens)
    events = []

    async for event in parse_stream(stream):
        events.append(event)

    # Validate CALLS parsing
    calls_events = [e for e in events if e["type"] == "calls"]
    yield_events = [e for e in events if e["type"] == "yield"]

    assert len(calls_events) == 1
    assert len(yield_events) == 1

    # JSON should be parsed into calls field
    calls_data = calls_events[0]["calls"]
    assert isinstance(calls_data, list)
    assert len(calls_data) == 1
    assert calls_data[0]["name"] == "search"
    assert calls_data[0]["args"]["query"] == "python basics"

    # YIELD after CALLS should have execute context
    assert yield_events[0]["content"] == "execute"


@pytest.mark.asyncio
async def test_parser_with_malformed_calls_json():
    """Test parser with malformed JSON in CALLS section."""

    # Invalid JSON in calls
    malformed_tokens = [
        "§CALLS",
        "\n",
        '{"name": "tool", "args": {',  # Missing closing
        "§RESPOND",
        "\n",
        "Continuing after error",
    ]

    stream = MockStream(malformed_tokens)
    events = []

    async for event in parse_stream(stream):
        events.append(event)

    # Parser should generate error event and continue
    error_events = [e for e in events if e["type"] == "error"]
    respond_events = [e for e in events if e["type"] == "respond"]

    assert len(error_events) == 1
    assert len(respond_events) == 1

    # Error should describe JSON problem
    assert "Invalid JSON" in error_events[0]["content"]

    # Parser should continue processing
    assert respond_events[0]["content"] == "Continuing after error"


@pytest.mark.asyncio
async def test_parser_yield_context_awareness():
    """Test context-aware YIELD generation based on preceding delimiter."""

    # Test YIELD after CALLS = execute
    tokens_calls = ["§CALLS", "\n", "[]", "§YIELD"]
    stream = MockStream(tokens_calls)
    events = [event async for event in parse_stream(stream)]

    yield_events = [e for e in events if e["type"] == "yield"]
    assert len(yield_events) == 1
    assert yield_events[0]["content"] == "execute"

    # Test YIELD after RESPOND = complete
    tokens_respond = ["§RESPOND", "\n", "Done", "§YIELD"]
    stream = MockStream(tokens_respond)
    events = [event async for event in parse_stream(stream)]

    yield_events = [e for e in events if e["type"] == "yield"]
    assert len(yield_events) == 1
    assert yield_events[0]["content"] == "complete"


@pytest.mark.asyncio
async def test_parser_streaming_content_preservation():
    """Test that parser preserves content exactly as received from providers."""

    # Test with various content patterns observed from real providers
    content_patterns = [
        # OpenAI chunking pattern
        ["§THINK", " ", "2", " +", " ", "2", " is", " a", " basic", " arithmetic", " problem", "."],
        # Gemini response pattern
        ["§RESPOND", "\n", "The", " answer", " is", " ", "4", "."],
        # Mixed whitespace handling
        ["§THINK", "\n\n", "Multiple", "\n", "lines", "\n", "of reasoning", "\n\n"],
    ]

    for pattern in content_patterns:
        stream = MockStream(pattern + ["§YIELD"])
        events = []

        async for event in parse_stream(stream):
            events.append(event)

        # Content should be preserved across all chunks (parser strips per event)
        content_events = [e for e in events if e["type"] in ["think", "respond"]]

        # Parser strips whitespace from each individual chunk/event
        # So we validate that non-whitespace content is preserved
        total_content = "".join(e["content"] for e in content_events)

        # Should preserve meaningful content (whitespace handling is implementation detail)
        meaningful_tokens = [token for token in pattern[1:] if token.strip()]
        for token in meaningful_tokens:
            if token.strip():  # Only check non-whitespace tokens
                assert token.strip() in total_content


@pytest.mark.asyncio
async def test_parser_performance_with_large_streams():
    """Test parser performance with large token streams (simulating long responses)."""

    # Simulate large response (1000 tokens)
    large_tokens = ["§THINK", "\n"]

    # Add many content tokens
    for i in range(1000):
        large_tokens.append(f"Token {i} with some content. ")

    large_tokens.extend(["§RESPOND", "\n", "Final answer", "§YIELD"])

    stream = MockStream(large_tokens)
    events = []

    # Should complete without timeout
    async for event in parse_stream(stream):
        events.append(event)

    # Should have processed all tokens
    think_events = [e for e in events if e["type"] == "think"]
    respond_events = [e for e in events if e["type"] == "respond"]
    yield_events = [e for e in events if e["type"] == "yield"]

    assert len(think_events) == 1000  # One event per token
    assert len(respond_events) == 1
    assert len(yield_events) == 1

    # Content should be preserved
    total_think_content = "".join(e["content"] for e in think_events)
    assert "Token 0" in total_think_content
    assert "Token 999" in total_think_content
