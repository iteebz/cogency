"""Test that parser hardstoops on execute/end signals.

This is a critical safety mechanism for both replay and resume modes:
when the LLM emits §execute or §end, the token stream must terminate
immediately without consuming remaining tokens.

Parser hardstop ensures:
- §execute: Tool invocation boundary - stops stream before tool execution
- §end: Task completion boundary - stops stream at natural finish

This is mode-agnostic because parse_tokens() is shared infrastructure.
"""

import pytest

from cogency import Agent


@pytest.mark.asyncio
async def test_stream_hardstops_on_execute(mock_llm, mock_tool):
    """Parser must terminate when §execute is parsed, not continue consuming tokens."""

    babble_after_execute = "this should not be parsed as a tool call or response"

    protocol_tokens = [
        '§call: {"name": "test_tool", "args": {"message": "clean call"}}\n',
        "§execute\n",
        babble_after_execute,  # These tokens must NOT be consumed
        "§respond: Response after execute\n",
        "§end\n",
    ]

    llm = mock_llm.set_response_tokens(protocol_tokens)
    agent = Agent(llm=llm, tools=[mock_tool()], mode="replay", max_iterations=1)

    events = [event async for event in agent("Test query", stream="event")]

    call_event = next((e for e in events if e["type"] == "call"), None)
    execute_event = next((e for e in events if e["type"] == "execute"), None)

    assert call_event is not None, "Should have call event"
    assert execute_event is not None, "Should have execute event"

    # Babble should NOT appear in any parsed event
    all_content = " ".join(str(e.get("content", "")) + str(e.get("payload", "")) for e in events)
    assert babble_after_execute not in all_content, (
        "Stream did not hardstop on execute - babble was parsed"
    )


@pytest.mark.asyncio
async def test_stream_hardstops_on_end(mock_llm, mock_tool):
    """Parser must terminate when §end is parsed, not continue consuming tokens."""

    babble_after_end = "this should definitely not be processed"

    protocol_tokens = [
        "§respond: Final response\n",
        "§end\n",
        babble_after_end,  # These tokens must NOT be consumed
        '§call: {"name": "fake", "args": {}}\n',  # Should not be parsed
    ]

    llm = mock_llm.set_response_tokens(protocol_tokens)
    agent = Agent(llm=llm, tools=[mock_tool()], mode="replay", max_iterations=1)

    events = [event async for event in agent("Test query", stream="event")]

    end_event = next((e for e in events if e["type"] == "end"), None)
    assert end_event is not None, "Should have end event"

    # No call event should exist (babble was not consumed)
    call_events = [e for e in events if e["type"] == "call"]
    assert len(call_events) == 0, "Stream did not hardstop on end - found unexpected call events"

    # Babble should not appear
    all_content = " ".join(str(e.get("content", "")) + str(e.get("payload", "")) for e in events)
    assert babble_after_end not in all_content, "Stream did not hardstop on end - babble was parsed"


@pytest.mark.asyncio
async def test_token_consumption_boundary_execute(mock_llm, mock_tool):
    """Verify parser stops consuming at §execute by tracking token flow."""

    tokens_seen = []

    class InstrumentedMockLLM:
        http_model = "test"

        def __init__(self, response_tokens):
            self.response_tokens = response_tokens

        async def generate(self, messages):
            return "".join(self.response_tokens)

        async def stream(self, messages):
            """Track which tokens are actually consumed."""
            for token in self.response_tokens:
                tokens_seen.append(token)
                yield token

    protocol_tokens = [
        '§call: {"name": "test_tool", "args": {"message": "test"}}\n',
        "§execute\n",
        "SHOULD_NOT_SEE_THIS",
        "§respond: after\n",
        "§end\n",
    ]

    llm = InstrumentedMockLLM(protocol_tokens)
    agent = Agent(llm=llm, tools=[mock_tool()], mode="replay", max_iterations=1)

    [event async for event in agent("Test", stream="event")]

    # Should see tokens up through and including §execute\n
    assert "§execute\n" in tokens_seen

    # Should NOT see tokens after §execute\n
    assert "SHOULD_NOT_SEE_THIS" not in tokens_seen


@pytest.mark.asyncio
async def test_token_consumption_boundary_end(mock_llm, mock_tool):
    """Verify parser stops consuming at §end without consuming remaining tokens."""

    tokens_seen = []

    class InstrumentedMockLLM:
        http_model = "test"

        def __init__(self, response_tokens):
            self.response_tokens = response_tokens

        async def generate(self, messages):
            return "".join(self.response_tokens)

        async def stream(self, messages):
            """Track which tokens are actually consumed."""
            for token in self.response_tokens:
                tokens_seen.append(token)
                yield token

    protocol_tokens = [
        "§respond: Final answer\n",
        "§end\n",
        "DEFINITELY_NOT_SEEN",
        '§call: {"bad": "data"}\n',
    ]

    llm = InstrumentedMockLLM(protocol_tokens)
    agent = Agent(llm=llm, tools=[mock_tool()], mode="replay", max_iterations=1)

    [event async for event in agent("Test", stream="event")]

    # Should see tokens up through and including §end\n
    assert "§end\n" in tokens_seen

    # Should NOT see tokens after §end\n
    assert "DEFINITELY_NOT_SEEN" not in tokens_seen
