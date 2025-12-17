"""Resume mode iteration accounting.

Contract: max_iterations counts tool execution turns, not streamed events.
- One turn = LLM response until tool execution boundary (<execute>) or completion
- Multiple think/respond/call events in single LLM response = one turn
- Turn increments only when tool result completes (allowing next LLM request)
- Boundary: exactly max_iterations should complete; max_iterations+1 should fail
"""

import pytest

from cogency.core.errors import LLMError
from cogency.resume import stream as resume_stream


@pytest.mark.asyncio
async def test_one_turn(mock_llm, mock_config):
    """One LLM response = one turn."""
    mock_llm.set_response_tokens(
        [
            "<think>Analyzing requirement</think>",
            "<think>Planning approach</think>",
            "Here is the solution",
            "It works like this",
        ]
    )
    mock_config.max_iterations = 1

    events = []
    async for event in resume_stream("test", "user", "conv", config=mock_config):
        events.append(event)

    assert any(e["type"] == "respond" for e in events)


@pytest.mark.asyncio
async def test_boundary_exact(mock_config, resume_llm):
    """Completes at exact iteration limit."""
    mock_config.llm = resume_llm(
        [
            ["Response 1"],
        ]
    )
    mock_config.max_iterations = 1

    events = []
    async for event in resume_stream("test", "user", "conv", config=mock_config):
        events.append(event)

    assert any(e["type"] == "respond" for e in events)


@pytest.mark.asyncio
async def test_iteration_limit(mock_config, mock_tool, resume_llm):
    """Second turn exceeds max_iterations."""
    tool = mock_tool().configure(name="test_tool")
    mock_config.tools = [tool]
    mock_config.llm = resume_llm(
        [
            [
                "<think>need tool</think>",
                f'<execute>[{{"name": "{tool.name}", "args": {{"message": "hi"}}}}]</execute>',
            ],
            [
                "tool done",
            ],
        ]
    )
    mock_config.max_iterations = 1

    with pytest.raises(LLMError, match="Max iterations"):
        async for _ in resume_stream("test", "user", "conv", config=mock_config):
            pass


@pytest.mark.asyncio
async def test_continuation_within_limit(mock_config, mock_tool, resume_llm):
    """Tool continuation succeeds within limits."""
    tool = mock_tool().configure(name="test_tool")
    mock_config.tools = [tool]
    mock_config.llm = resume_llm(
        [
            [
                "<think>need tool</think>",
                f'<execute>[{{"name": "{tool.name}", "args": {{"message": "hi"}}}}]</execute>',
            ],
            [
                "tool done",
            ],
        ]
    )
    mock_config.max_iterations = 2

    events = []
    async for event in resume_stream("test", "user", "conv", config=mock_config):
        events.append(event)

    assert any(e["type"] == "result" for e in events), "Expected tool result event"
    assert any(e["type"] == "respond" for e in events)
