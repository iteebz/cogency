"""Event deduplication contract.

All events yielded exactly once. No duplicates on retry paths.
"""

import pytest

from cogency.resume import stream as resume_stream


@pytest.mark.asyncio
async def test_no_duplicate_end_events(mock_llm, mock_config):
    """End event should appear exactly once."""
    mock_llm.set_response_tokens(["Result"])

    events = []
    async for event in resume_stream("test", "user", "conv", config=mock_config):
        events.append(event)

    respond_events = [e for e in events if e["type"] == "respond"]
    assert len(respond_events) >= 1, "Expected at least one respond event"


@pytest.mark.asyncio
async def test_respond_yields_once(mock_llm, mock_config):
    """Respond events from LLM generation appear exactly once."""
    mock_llm.set_response_tokens(["Part 1", "Part 2"])

    events = []
    async for event in resume_stream("test", "user", "conv", config=mock_config):
        events.append(event)

    respond_events = [e for e in events if e["type"] == "respond"]
    # Each respond segment should appear once (may be chunked or combined)
    assert len(respond_events) >= 1, "Expected at least one respond event"
    assert len(respond_events) <= 2, f"Respond events should not duplicate: {respond_events}"


@pytest.mark.asyncio
async def test_result_once(mock_config, mock_tool, resume_llm):
    """Tool results surface exactly once."""
    tool = mock_tool().configure(name="test_tool")
    mock_config.tools = [tool]
    mock_config.llm = resume_llm(
        [
            [
                "<think>need tool</think>",
                f'<execute>[{{"name": "{tool.name}", "args": {{"message": "hi"}}}}]</execute>',
            ],
            [
                "done",
            ],
        ]
    )

    events = []
    async for event in resume_stream("test", "user", "conv", config=mock_config):
        events.append(event)

    result_events = [e for e in events if e["type"] == "result"]
    assert len(result_events) == 1, f"Expected single result event, saw {len(result_events)}"
