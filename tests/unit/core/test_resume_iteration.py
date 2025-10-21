"""Resume mode iteration accounting.

Contract: max_iterations counts tool execution turns, not streamed events.
- One turn = LLM response until tool execution boundary (§execute) or completion (§end)
- Multiple think/respond/call events in single LLM response = one turn
- Turn increments only when tool result completes (allowing next LLM request)
- Boundary: exactly max_iterations should complete; max_iterations+1 should fail
"""

import pytest

from cogency.core.resume import stream as resume_stream


@pytest.mark.asyncio
async def test_single_response_multiple_events_one_turn(mock_llm, mock_config):
    """One LLM response with multiple events = one turn."""
    mock_llm.set_response_tokens(
        [
            "§think: Analyzing requirement\n",
            "§think: Planning approach\n",
            "§respond: Here is the solution\n",
            "§respond: It works like this\n",
            "§end\n",
        ]
    )
    mock_config.max_iterations = 1

    events = []
    async for event in resume_stream("test", "user", "conv", config=mock_config):
        events.append(event)

    assert any(e["type"] == "respond" for e in events)
    assert any(e["type"] == "end" for e in events)


@pytest.mark.asyncio
async def test_iteration_boundary_exact_limit(mock_config, resume_llm):
    """Completes exactly at configured iteration limit."""
    mock_config.llm = resume_llm(
        [
            ["§respond: Response 1\n", "§end\n"],
        ]
    )
    mock_config.max_iterations = 1

    events = []
    async for event in resume_stream("test", "user", "conv", config=mock_config):
        events.append(event)

    assert any(e["type"] == "end" for e in events)


@pytest.mark.asyncio
async def test_tool_continuation_hits_iteration_limit(mock_config, mock_tool, resume_llm):
    """Second turn (after tool result) trips max_iterations guard."""
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
                "§respond: tool done\n",
                "§end\n",
            ],
        ]
    )
    mock_config.max_iterations = 1

    with pytest.raises(RuntimeError, match="Max iterations"):
        async for _ in resume_stream("test", "user", "conv", config=mock_config):
            pass


@pytest.mark.asyncio
async def test_tool_continuation_within_limit(mock_config, mock_tool, resume_llm):
    """Two-turn tool flow succeeds when iterations allow it."""
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
                "§respond: tool done\n",
                "§end\n",
            ],
        ]
    )
    mock_config.max_iterations = 2

    events = []
    async for event in resume_stream("test", "user", "conv", config=mock_config):
        events.append(event)

    assert any(e["type"] == "result" for e in events), "Expected tool result event"
    assert any(e["type"] == "respond" for e in events)
    assert any(e["type"] == "end" for e in events)
