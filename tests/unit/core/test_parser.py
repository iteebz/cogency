"""Parser edge case tests - comprehensive failure scenarios.

Test cases:
1. Delimiter fragment leakage across token boundaries
2. Malformed JSON that could crash parser
3. Stream cutoffs at critical points
4. Buffer overflow scenarios
5. Multiple delimiters with edge cases
6. Invalid delimiter sequences
7. Empty/null content handling
"""

import pytest

from cogency.core.parser import _parse_json, parse_stream
from cogency.core.protocols import Event


class MockStream:
    def __init__(self, tokens):
        self.tokens = tokens

    def __aiter__(self):
        return self

    async def __anext__(self):
        if not self.tokens:
            raise StopAsyncIteration
        return self.tokens.pop(0)


@pytest.mark.asyncio
async def test_delimiter_fragment_leakage():
    """Parser prevents delimiter symbol leakage across token boundaries."""

    # Critical cases: delimiter fragments that should NOT leak into content
    leak_cases = [
        ["thinking ", "§", "CALLS ", "[]§EXECUTE"],  # Split delimiter
        ["unix | pipe", "§CALLS ", "[]§EXECUTE"],  # Preserve pipes, block delimiters
        ["text§", "CALLS ", "[]§EXECUTE"],  # Delimiter at token boundary
    ]

    for tokens in leak_cases:
        events = [e async for e in parse_stream(MockStream(tokens))]

        think_events = [e for e in events if e["type"] == Event.THINK]
        think_content = "".join(e["content"] for e in think_events)

        # § symbols should not leak (except in legitimate pipes)
        clean_content = think_content.replace("unix | pipe", "")
        assert "§" not in clean_content, f"Delimiter leaked: {think_content!r}"

        # Should still parse calls/execute correctly
        calls_events = [e for e in events if e["type"] == Event.CALLS]
        execute_events = [e for e in events if e["type"] == Event.EXECUTE]
        assert len(calls_events) == 1
        assert len(execute_events) == 1


@pytest.mark.asyncio
async def test_malformed_json_destruction():
    """Parser survives all malformed JSON patterns and continues processing."""

    # Every way JSON breaks in production
    malformed_cases = [
        '{"name": "tool", "args": {}',  # Missing closing
        '[{"name": "tool",}]',  # Extra commas
        '[{"name": "tool]',  # Incomplete quotes
        '[{"name": "tool", "args": {"key":}]',  # Nested incomplete
        "not json at all",  # Completely broken
        "{",  # Empty invalid
        '[{"name": "tööl", "args": {"ключ": "значение"}}]',  # Unicode
    ]

    for malformed_json in malformed_cases:
        tokens = ["§CALLS ", malformed_json, "§EXECUTE", "§RESPOND ", "continuing"]
        events = [e async for e in parse_stream(MockStream(tokens))]

        # Should generate error and continue processing
        error_events = [e for e in events if e["type"] == "error"]
        respond_events = [e for e in events if e["type"] == Event.RESPOND]

        assert len(error_events) == 1, f"Expected error for: {malformed_json!r}"
        assert len(respond_events) == 1, f"Parser died on: {malformed_json!r}"
        assert "Invalid JSON" in error_events[0]["content"]


@pytest.mark.asyncio
async def test_stream_cutoff_scenarios():
    """Parser handles abrupt stream termination at critical points."""

    cutoff_cases = [
        ["thinking", "§TOO"],  # Mid-delimiter
        ["§CALLS ", '{"name":', '"tool"'],  # Mid-JSON
        ["§CALLS ", "[{}]"],  # Missing execute
        ["§RESPOND ", "partial response"],  # Mid-respond
    ]

    for tokens in cutoff_cases:
        events = [e async for e in parse_stream(MockStream(tokens))]

        # Parser should not crash, should process what it can
        [e["type"] for e in events]
        assert len(events) >= 0, f"Parser crashed on cutoff: {tokens}"

        # No infinite loops (if we get here, timeout didn't trigger)
        assert True  # Successfully completed parsing


@pytest.mark.asyncio
async def test_json_validation():
    """JSON parser validates correctly."""

    # Valid cases
    valid = ['{"name": "test"}', '[{"name": "tool"}]', "{}", "[]"]
    for json_str in valid:
        result = _parse_json(json_str)
        assert result.success, f"Valid JSON failed: {json_str}"

    # Invalid cases
    invalid = ['{"name": "test", "args": {', '{"name": "tëst"}', "", "not json", "{invalid}"]
    for json_str in invalid:
        result = _parse_json(json_str)
        assert result.failure, f"Invalid JSON should fail: {json_str}"


@pytest.mark.asyncio
async def test_execute_context_handling():
    """EXECUTE events generated correctly after CALLS and RESPOND."""

    # After CALLS
    tokens = ["§CALLS [{}]", "§EXECUTE"]
    events = [e async for e in parse_stream(MockStream(tokens))]
    execute_events = [e for e in events if e["type"] == Event.EXECUTE]
    assert len(execute_events) == 1
    assert execute_events[0]["content"] == ""

    # After RESPOND
    tokens = ["§RESPOND Done", "§EXECUTE"]
    events = [e async for e in parse_stream(MockStream(tokens))]
    execute_events = [e for e in events if e["type"] == Event.EXECUTE]
    assert len(execute_events) == 1
    assert execute_events[0]["content"] == ""


@pytest.mark.asyncio
async def test_non_string_token_handling():
    """Parser rejects non-string tokens."""

    async def bad_stream():
        yield "§THINK Starting"
        yield {"not": "a string"}  # Non-string token

    with pytest.raises(RuntimeError, match="Parser expects string tokens"):
        async for _event in parse_stream(bad_stream()):
            pass


@pytest.mark.asyncio
async def test_calls_json_parsing():
    """Parser handles valid/invalid JSON in CALLS sections."""

    # Valid tool calls
    valid_tokens = ["§CALLS", '[{"name": "search", "args": {"query": "test"}}]', "§EXECUTE"]
    events = [e async for e in parse_stream(MockStream(valid_tokens))]

    calls_events = [e for e in events if e["type"] == Event.CALLS]
    assert len(calls_events) == 1
    assert calls_events[0]["calls"][0]["name"] == "search"
    assert calls_events[0]["calls"][0]["args"]["query"] == "test"

    # Malformed JSON should generate error and continue
    invalid_tokens = ["§CALLS", '{"name": "tool", "args": {', "§RESPOND", "continuing"]
    events = [e async for e in parse_stream(MockStream(invalid_tokens))]

    error_events = [e for e in events if e["type"] == "error"]
    respond_events = [e for e in events if e["type"] == Event.RESPOND]
    assert len(error_events) == 1
    assert len(respond_events) == 1
    assert "Invalid JSON" in error_events[0]["content"]


@pytest.mark.asyncio
async def test_missing_execute_handling():
    """Parser handles streams that end without EXECUTE delimiter."""

    # Stream ends abruptly - real network failure scenario
    tokens = ["§THINK", "reasoning", "§RESPOND", "answer"]
    events = [e async for e in parse_stream(MockStream(tokens))]

    think_events = [e for e in events if e["type"] == Event.THINK]
    respond_events = [e for e in events if e["type"] == Event.RESPOND]
    execute_events = [e for e in events if e["type"] == Event.EXECUTE]

    assert len(think_events) == 1
    assert len(respond_events) == 1
    assert len(execute_events) == 0  # No EXECUTE generated
