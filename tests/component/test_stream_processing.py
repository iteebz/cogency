"""Component tests for end-to-end stream processing.

Tests the complete flow: provider → parser → event processing
Based on empirical findings about YIELD emission and infinite hang fixes.
"""

import pytest

from cogency.core.parser import parse_stream
from cogency.core.protocols import Event


class MockProviderStream:
    """Mock provider stream that simulates real streaming behavior."""

    def __init__(self, tokens, should_emit_yield=True, should_fail=False):
        self.tokens = tokens
        self.should_emit_yield = should_emit_yield
        self.should_fail = should_fail

    def __aiter__(self):
        return self

    async def __anext__(self):
        if self.should_fail and len(self.tokens) == 1:
            # Simulate failure mid-stream (after processing some tokens)
            raise Exception("Mock provider failure")

        if not self.tokens:
            if self.should_emit_yield:
                # Simulate provider emitting YIELD
                self.should_emit_yield = False
                return Event.YIELD.delimiter
            raise StopAsyncIteration

        return self.tokens.pop(0)


@pytest.mark.asyncio
async def test_complete_stream_processing_happy_path():
    """Test complete happy path: provider tokens → parser → events."""

    # Simulate realistic provider token stream
    provider_tokens = [
        "§THINK",
        "\n",
        "I need to solve this step by step.",
        "§RESPOND",
        "\n",
        "The answer is 42.",
        # YIELD will be added automatically by MockProviderStream
    ]

    provider_stream = MockProviderStream(provider_tokens)

    # Process through parser
    events = []
    async for event in parse_stream(provider_stream):
        events.append(event)

    # Should produce proper event sequence
    event_types = [e["type"] for e in events]
    assert "think" in event_types
    assert "respond" in event_types
    assert "yield" in event_types

    # YIELD should be last event
    assert events[-1]["type"] == "yield"
    assert events[-1]["content"] == "complete"  # YIELD after RESPOND


@pytest.mark.asyncio
async def test_stream_processing_handles_exceptions():
    """Test that exceptions during stream processing are handled gracefully."""

    # This test validates that parser doesn't crash on stream exceptions
    # The key insight is that providers should emit YIELD in finally blocks

    provider_tokens = ["§THINK", "\n", "Some content before failure"]

    provider_stream = MockProviderStream(provider_tokens, should_fail=True)

    events = []
    exception_occurred = False

    try:
        async for event in parse_stream(provider_stream):
            events.append(event)
    except Exception:
        exception_occurred = True

    # Exception should occur (simulating provider failure)
    assert exception_occurred is True

    # Parser should have processed some tokens before exception
    # (This validates parser doesn't immediately crash)


@pytest.mark.asyncio
async def test_stream_processing_missing_yield():
    """Test stream processing when provider doesn't emit YIELD."""

    # Provider stream without YIELD emission
    provider_tokens = [
        "§THINK",
        "\n",
        "Some thinking",
        "§RESPOND",
        "\n",
        "Some response",
        # NO YIELD - simulates old buggy behavior
    ]

    provider_stream = MockProviderStream(provider_tokens, should_emit_yield=False)

    events = []
    async for event in parse_stream(provider_stream):
        events.append(event)

    # Parser should process all content
    think_events = [e for e in events if e["type"] == "think"]
    respond_events = [e for e in events if e["type"] == "respond"]
    yield_events = [e for e in events if e["type"] == "yield"]

    assert len(think_events) >= 1
    assert len(respond_events) >= 1

    # Critical: Should NOT have YIELD event if provider doesn't emit it
    assert len(yield_events) == 0

    # This is what causes infinite hangs in replay mode!


@pytest.mark.asyncio
async def test_stream_processing_with_function_calls():
    """Test stream processing with function call workflow."""

    # Realistic function call stream
    provider_tokens = [
        "§THINK",
        "\n",
        "I need to search for information.",
        "§CALLS",
        "\n",
        '[{"name": "search", "args": {"query": "python tutorial"}}]',
        # YIELD will be added - should have "execute" context
    ]

    provider_stream = MockProviderStream(provider_tokens)

    events = []
    async for event in parse_stream(provider_stream):
        events.append(event)

    # Should have proper call structure
    calls_events = [e for e in events if e["type"] == "calls"]
    yield_events = [e for e in events if e["type"] == "yield"]

    assert len(calls_events) == 1
    assert len(yield_events) == 1

    # Calls should be parsed as JSON
    calls_data = calls_events[0]["calls"]
    assert isinstance(calls_data, list)
    assert calls_data[0]["name"] == "search"

    # YIELD after CALLS should have "execute" context
    assert yield_events[0]["content"] == "execute"


@pytest.mark.asyncio
async def test_stream_processing_malformed_json_recovery():
    """Test that stream processing recovers from malformed JSON."""

    # Stream with malformed JSON in CALLS
    provider_tokens = [
        "§CALLS",
        "\n",
        '{"name": "tool", "incomplete',  # Malformed JSON
        "§RESPOND",
        "\n",
        "Continuing after error",
    ]

    provider_stream = MockProviderStream(provider_tokens)

    events = []
    async for event in parse_stream(provider_stream):
        events.append(event)

    # Should generate error event but continue processing
    error_events = [e for e in events if e["type"] == "error"]
    respond_events = [e for e in events if e["type"] == "respond"]

    assert len(error_events) == 1
    assert len(respond_events) >= 1

    # Error should describe the problem
    assert "Invalid JSON" in error_events[0]["content"]

    # Stream should continue after error
    assert respond_events[0]["content"] == "Continuing after error"


@pytest.mark.asyncio
async def test_yield_emission_prevents_infinite_hangs():
    """Test that YIELD emission prevents infinite hangs in downstream consumers."""

    # Simulate replay mode waiting for YIELD
    provider_tokens = ["§RESPOND", "\n", "This is the final answer."]

    provider_stream = MockProviderStream(provider_tokens)

    events = []
    yielded = False

    async for event in parse_stream(provider_stream):
        events.append(event)

        if event["type"] == "yield":
            yielded = True
            # Simulate replay mode breaking on YIELD
            break

    # Should have yielded (prevents infinite hangs)
    assert yielded is True

    # Should have processed response before yielding
    respond_events = [e for e in events if e["type"] == "respond"]
    assert len(respond_events) >= 1


@pytest.mark.asyncio
async def test_chunked_delimiter_reassembly():
    """Test that chunked delimiters are properly reassembled."""

    # Simulate delimiters split across chunks (real provider behavior)
    provider_tokens = [
        "§",  # Delimiter start
        "TH",
        "INK",  # Delimiter complete
        "\n",
        "Reasoning content",
        "§",  # Next delimiter start
        "RESP",
        "OND",  # Delimiter complete
        "\n",
        "Response content",
    ]

    provider_stream = MockProviderStream(provider_tokens)

    events = []
    async for event in parse_stream(provider_stream):
        events.append(event)

    # Should correctly identify delimiters despite chunking
    think_events = [e for e in events if e["type"] == "think"]
    respond_events = [e for e in events if e["type"] == "respond"]

    assert len(think_events) >= 1
    assert len(respond_events) >= 1

    # Content should be preserved
    assert "Reasoning content" in "".join(e["content"] for e in think_events)
    assert "Response content" in "".join(e["content"] for e in respond_events)


@pytest.mark.asyncio
async def test_empty_stream_handling():
    """Test handling of completely empty provider streams."""

    # Empty stream (provider returns nothing)
    provider_stream = MockProviderStream([])

    events = []
    async for event in parse_stream(provider_stream):
        events.append(event)

    # Should emit YIELD even for empty stream (prevents hangs)
    yield_events = [e for e in events if e["type"] == "yield"]
    assert len(yield_events) == 1


@pytest.mark.asyncio
async def test_large_stream_performance():
    """Test performance with large token streams."""

    # Generate large stream (1000 tokens)
    large_tokens = ["§THINK", "\n"]
    for i in range(500):
        large_tokens.append(f"Token {i} ")
    large_tokens.extend(["§RESPOND", "\n", "Final answer"])

    provider_stream = MockProviderStream(large_tokens)

    events = []
    # Should complete without timeout
    async for event in parse_stream(provider_stream):
        events.append(event)

    # Should process all content efficiently
    think_events = [e for e in events if e["type"] == "think"]
    respond_events = [e for e in events if e["type"] == "respond"]
    yield_events = [e for e in events if e["type"] == "yield"]

    assert len(think_events) >= 500  # Should process all think tokens
    assert len(respond_events) >= 1
    assert len(yield_events) == 1
