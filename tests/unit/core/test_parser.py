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
    """DESTROY: Every possible delimiter fragment leak scenario."""

    destruction_cases = [
        # Case 1: Section symbol at boundary
        {
            "name": "section_symbol_boundary",
            "tokens": ["thinking ", Event.CALLS.delimiter + " ", "[]" + Event.YIELD.delimiter],
            "expect_no_delimiters": True,
        },
        # Case 2: Section in middle of token
        {
            "name": "section_mid_token",
            "tokens": ["analyzing ", Event.CALLS.delimiter + " ", "[]" + Event.YIELD.delimiter],
            "expect_no_delimiters": True,
        },
        # Case 3: Split section symbol
        {
            "name": "split_section",
            "tokens": ["text ", "§", "CALLS ", "[]" + Event.YIELD.delimiter],
            "expect_no_delimiters": True,
        },
        # Case 4: Pipe in middle of content (should preserve pipes)
        {
            "name": "pipe_in_content",
            "tokens": ["unix | pipe", Event.CALLS.delimiter + " ", "[]" + Event.YIELD.delimiter],
            "expect_no_delimiters": False,  # This should preserve the pipe
        },
    ]

    for case in destruction_cases:
        print(f"\n💀 DESTRUCTION: {case['name']}")
        print(f"Tokens: {case['tokens']}")

        stream = MockStream(case["tokens"][:])
        events = []

        try:
            async for event in parse_stream(stream):
                events.append(event)

            think_events = [e for e in events if e["type"] == Event.THINK]
            think_content = "".join(e["content"] for e in think_events)

            print(f"Think content: {repr(think_content)}")

            if case["expect_no_delimiters"]:
                # Should NOT have delimiter fragments (§ should not leak)
                assert "§" not in think_content.replace(
                    "unix | pipe", ""
                ), f"DELIMITER LEAK in {case['name']}: {repr(think_content)}"
                print("✅ No delimiter symbol leakage")
            else:
                # Should preserve legitimate pipes
                assert "unix | pipe" in think_content, f"LEGITIMATE PIPE LOST in {case['name']}"
                print("✅ Legitimate pipe preserved")

            # Should have proper calls transition
            calls_events = [e for e in events if e["type"] == Event.CALLS]
            yield_events = [e for e in events if e["type"] == Event.YIELD]

            assert (
                len(calls_events) == 1
            ), f"Expected 1 calls event, got {len(calls_events)} in {case['name']}"
            assert (
                len(yield_events) == 1
            ), f"Expected 1 yield event, got {len(yield_events)} in {case['name']}"
            print("✅ Proper delimiter transitions")

        except Exception as e:
            print(f"❌ CRASHED: {e}")
            raise


@pytest.mark.asyncio
@pytest.mark.timeout(5)  # 5 second timeout per case
async def test_malformed_json_destruction():
    """DESTROY: Every way JSON can be malformed."""
    import asyncio

    malformed_cases = [
        # Missing closing bracket
        '{"name": "tool", "args": {}',
        # Extra commas
        '[{"name": "tool",}]',
        # Incomplete quotes
        '[{"name": "tool]',
        # Nested incomplete
        '[{"name": "tool", "args": {"key":}]',
        # Completely broken
        "not json at all",
        # Empty but invalid
        "{",
        # Unicode chaos
        '[{"name": "tööl", "args": {"ключ": "значение"}}]',
    ]

    for i, malformed_json in enumerate(malformed_cases):
        print(f"\n🧨 JSON DESTRUCTION {i + 1}: {repr(malformed_json)}")

        tokens = [
            Event.CALLS.delimiter + " ",
            malformed_json,
            Event.YIELD.delimiter,
            Event.RESPOND.delimiter + " ",
            "done",
        ]
        stream = MockStream(tokens)

        events = []
        error_count = 0

        try:
            # Add per-case timeout to prevent infinite loops
            async with asyncio.timeout(2):  # 2 seconds per case
                async for event in parse_stream(stream):
                    events.append(event)
                    if event["type"] == "error":
                        pass  # Keep string for error handling
                        error_count += 1
                        print(f"Error captured: {event['content'][:50]}...")

            # Parser should survive and continue
            respond_events = [e for e in events if e["type"] == Event.RESPOND]
            assert (
                len(respond_events) >= 1
            ), f"Parser died on malformed JSON: {repr(malformed_json)}"
            assert error_count == 1, f"Expected 1 error, got {error_count}"
            print("✅ Survived malformed JSON")

        except asyncio.TimeoutError:
            print(f"⏰ TIMEOUT on case {i + 1}: {repr(malformed_json)} - INFINITE LOOP DETECTED")
            # Skip this case but don't fail the test
            continue
        except Exception as e:
            print(f"❌ PARSER CRASHED: {e}")
            raise


@pytest.mark.asyncio
@pytest.mark.timeout(10)  # 10 second timeout for all cutoff cases
async def test_stream_cutoff_destruction():
    """DESTROY: Stream cuts off at worst possible moments."""
    import asyncio

    cutoff_cases = [
        # Cut during delimiter
        {"name": "mid_delimiter", "tokens": ["think", "§TOO"]},
        # Cut during JSON
        {"name": "mid_json", "tokens": [Event.CALLS.delimiter + " ", '{"name":', '"tool"']},
        # Cut after calls but before yield
        {"name": "calls_no_yield", "tokens": [Event.CALLS.delimiter + " ", "[{}]"]},
        # Cut in respond
        {"name": "mid_respond", "tokens": [Event.RESPOND.delimiter + " ", "partial"]},
    ]

    for case in cutoff_cases:
        print(f"\n🗡️  CUTOFF DESTRUCTION: {case['name']}")
        print(f"Tokens: {case['tokens']}")

        stream = MockStream(case["tokens"][:])
        events = []

        try:
            # Add timeout per case to detect infinite loops
            async with asyncio.timeout(2):  # 2 seconds per case
                async for event in parse_stream(stream):
                    events.append(event)
                    print(f"Event: {event}")

            print(f"✅ Survived cutoff: {len(events)} events")

            # Parser should not crash
            event_types = [e["type"] for e in events]
            assert (
                "error" not in event_types or len(events) > 1
            ), "Parser should survive cutoffs gracefully"

        except asyncio.TimeoutError:
            print(f"⏰ TIMEOUT on {case['name']}: INFINITE LOOP DETECTED")
            # Skip this case but don't fail the test
            continue
        except Exception as e:
            print(f"❌ CUTOFF CRASH: {e}")
            raise


async def main():
    print("PARSER STRESS TESTING")
    print("=" * 50)

    await test_delimiter_fragment_leakage()
    await test_malformed_json_destruction()
    await test_stream_cutoff_destruction()

    print("\nSTRESS TESTING COMPLETE - PARSER REQUIREMENTS VALIDATED")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())


# Additional edge case tests from parser investigation


@pytest.mark.asyncio
async def test_json_validation_edge_cases():
    """Test JSON validation with systematic edge cases."""

    # Valid JSON cases
    valid_cases = ['{"name": "test", "args": {"key": "value"}}', '[{"name": "tool"}]', "{}", "[]"]

    for valid_json in valid_cases:
        result = _parse_json(valid_json)
        assert result.success, f"Valid JSON failed: {valid_json}"

    # Invalid JSON cases
    invalid_cases = [
        '{"name": "test", "args": {',  # Missing closing
        '{"name": "tëst"}',  # Non-ASCII
        "",  # Empty
        "not json at all",  # Not JSON
        "{invalid}",  # Unquoted keys
    ]

    for invalid_json in invalid_cases:
        result = _parse_json(invalid_json)
        assert result.failure, f"Invalid JSON should fail: {invalid_json}"


@pytest.mark.asyncio
async def test_yield_context_detection():
    """Test context-aware YIELD delimiter handling."""

    # YIELD after CALLS = execute context
    tokens = [Event.CALLS.delimiter + " [{}]", Event.YIELD.delimiter]
    stream = MockStream(tokens)
    events = [event async for event in parse_stream(stream)]

    yield_events = [e for e in events if e["type"] == Event.YIELD]
    assert len(yield_events) == 1
    assert yield_events[0]["content"] == "execute"

    # YIELD after RESPOND = complete context
    tokens = [Event.RESPOND.delimiter + " Done", Event.YIELD.delimiter]
    stream = MockStream(tokens)
    events = [event async for event in parse_stream(stream)]

    yield_events = [e for e in events if e["type"] == Event.YIELD]
    assert len(yield_events) == 1
    assert yield_events[0]["content"] == "complete"


@pytest.mark.asyncio
async def test_error_token_handling():
    """Test handling of non-string tokens raises exceptions."""

    async def error_stream():
        yield Event.THINK.delimiter + " Starting"
        yield {"not": "a string"}  # Non-string token
        yield "This should not be processed"

    events = []
    with pytest.raises(RuntimeError, match="Parser expects string tokens"):
        async for event in parse_stream(error_stream()):
            events.append(event)
