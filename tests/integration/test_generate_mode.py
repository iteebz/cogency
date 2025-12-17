"""Integration test for stream=None (.generate() mode) decomposition."""

from typing import TYPE_CHECKING, cast

import pytest

from cogency import Agent

if TYPE_CHECKING:
    from cogency.core.protocols import ResultEvent


@pytest.mark.asyncio
async def test_decompose_blob(mock_llm, mock_tool):
    """stream=None decomposes single blob into semantic events up to execute.

    Parser terminates after execute to force new iteration where model sees results.
    Response text after execute is discarded (would be generated before tool results).
    """
    complete_response = (
        "<think>reasoning here</think>"
        '<execute>[{"name": "test_tool", "args": {"message": "test"}}]</execute>'
    )

    mock_llm.generate.return_value = complete_response

    agent = Agent(llm=mock_llm, tools=[mock_tool()], mode="replay", max_iterations=1)
    events = [e async for e in agent("query", stream=None)]

    types = [e["type"] for e in events]
    assert "think" in types, "Should decompose think block from blob"
    assert "call" in types, "Should decompose call from blob"
    assert "execute" in types, "Should decompose execute from blob"
    assert "result" in types, "Should emit result after execution"

    user_idx = types.index("user")
    think_idx = types.index("think")
    call_idx = types.index("call")
    execute_idx = types.index("execute")
    result_idx = types.index("result")

    assert user_idx < think_idx
    assert call_idx < execute_idx
    assert execute_idx < result_idx

    think_events = [e for e in events if e["type"] == "think"]
    assert len(think_events) == 1
    think_event = think_events[0]
    assert think_event["type"] == "think"
    content = think_event.get("content", "")
    assert "reasoning here" in content


@pytest.mark.asyncio
async def test_batch_multi_tool(mock_llm, mock_tool):
    """stream=None handles multi-tool batches from single blob."""
    complete_response = (
        "<execute>["
        '{"name": "test_tool", "args": {"message": "first"}},'
        '{"name": "test_tool", "args": {"message": "second"}},'
        '{"name": "test_tool", "args": {"message": "third"}}'
        "]</execute>"
    )

    mock_llm.generate.return_value = complete_response

    agent = Agent(llm=mock_llm, tools=[mock_tool()], mode="replay", max_iterations=1)
    events = [e async for e in agent("query", stream=None)]

    # Should decompose into 3 call events
    call_events = [e for e in events if e["type"] == "call"]
    assert len(call_events) == 3

    # Single batched result
    result_events = [e for e in events if e["type"] == "result"]
    assert len(result_events) == 1

    result_event = cast("ResultEvent", result_events[0])
    assert result_event["type"] == "result"
    payload = result_event["payload"]
    assert payload is not None
    assert payload["tools_executed"] == 3
