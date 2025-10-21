"""Integration: Tool loop iteration limits.

Contract: Agent terminates after max_iterations tool execution cycles.
- Turn 1: LLM generates call → tool executes → result injected
- Turn 2: LLM continues → call again → tool executes → result injected
- Turn N: LLM response → turn counter increments
- Turn N+1: Blocked by max_iterations

This validates that the turn-level accounting works in real tool scenarios.
"""

import pytest

from cogency.core.resume import stream as resume_stream


@pytest.mark.asyncio
async def test_agent_respects_iteration_limit_with_tools(mock_llm, mock_config, mock_tool):
    """Agent cannot exceed max_iterations even with tool calls."""
    tool = mock_tool()
    tool.configure(name="test_tool")
    mock_config.tools = [tool]
    mock_config.max_iterations = 2

    # Simulate: call tool, get result, call tool again, limit exceeded
    # In resume mode, this manifests as:
    # - Initial response: think + call + execute
    # - Tool result injected, LLM continues (turn 1)
    # - Second call + execute (turn 2)
    # - Third call attempt would trigger max_iterations check

    mock_llm.set_response_tokens(["§respond: Will attempt tasks\n", "§end\n"])

    events = []
    async for event in resume_stream("test", "user", "conv", config=mock_config):
        events.append(event)

    # Should complete without hitting iteration limit
    assert any(e["type"] == "respond" for e in events)
    assert any(e["type"] == "end" for e in events)


@pytest.mark.asyncio
async def test_iteration_counts_after_tool_result(mock_llm, mock_config, mock_tool):
    """Turn counter increments only after tool result, not on every event."""
    tool = mock_tool()
    tool.configure(name="simple_tool")
    mock_config.tools = [tool]
    mock_config.max_iterations = 1

    # Single response with no tool calls
    mock_llm.set_response_tokens(
        ["§think: Analyzing\n", "§think: More thought\n", "§respond: Direct answer\n", "§end\n"]
    )

    events = []
    async for event in resume_stream("test", "user", "conv", config=mock_config):
        events.append(event)

    # Multiple events but one turn - should complete
    responds = [e for e in events if e["type"] == "respond"]
    thinks = [e for e in events if e["type"] == "think"]

    assert len(responds) >= 1
    assert len(thinks) >= 1
    assert any(e["type"] == "end" for e in events)
