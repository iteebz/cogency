"""Event deduplication contract.

All events yielded exactly once. No duplicates on retry paths.
"""

import pytest

from cogency.core.resume import stream as resume_stream


@pytest.mark.asyncio
async def test_no_duplicate_end_events(mock_llm, mock_config):
    """End event should appear exactly once."""
    mock_llm.set_response_tokens(["§respond: Result\n", "§end\n"])

    events = []
    async for event in resume_stream("test", "user", "conv", config=mock_config):
        events.append(event)

    end_count = sum(1 for e in events if e["type"] == "end")
    assert end_count == 1, f"Expected 1 end event, got {end_count}"


@pytest.mark.asyncio
async def test_respond_yields_once(mock_llm, mock_config):
    """Respond events from LLM generation appear exactly once."""
    mock_llm.set_response_tokens(["§respond: Part 1\n", "§respond: Part 2\n", "§end\n"])

    events = []
    async for event in resume_stream("test", "user", "conv", config=mock_config):
        events.append(event)

    respond_events = [e for e in events if e["type"] == "respond"]
    # Each respond segment should appear once (may be chunked or combined)
    assert len(respond_events) >= 1, "Expected at least one respond event"
    assert len(respond_events) <= 2, f"Respond events should not duplicate: {respond_events}"


@pytest.mark.asyncio
async def test_result_yields_once(mock_config, mock_tool, resume_llm):
    """Tool results surface exactly once before continuation."""
    tool = mock_tool().configure(name="test_tool")
    mock_config.tools = [tool]
    mock_config.llm = resume_llm(
        [
            [
                "§think: need tool\n",
                '§call: {"name": "test_tool", "args": {"message": "hi"}}\n',
                "§execute\n",
            ],
            [
                "§respond: done\n",
                "§end\n",
            ],
        ]
    )

    events = []
    async for event in resume_stream("test", "user", "conv", config=mock_config):
        events.append(event)

    result_events = [e for e in events if e["type"] == "result"]
    assert len(result_events) == 1, f"Expected single result event, saw {len(result_events)}"
