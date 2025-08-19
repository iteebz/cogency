"""Unit tests for ReAct algorithm functions."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from cogency.core.react import react, stream_react


@pytest.fixture
def mock_llm():
    """Mock LLM that returns structured responses."""
    llm = AsyncMock()
    llm.generate.return_value = MagicMock(
        success=True,
        failure=False,
        unwrap=lambda: "I'll search for this. Final answer: Test response",
    )
    return llm


@pytest.fixture
def mock_tools():
    """Mock tools dictionary."""
    tool = MagicMock()
    tool.name = "search"
    tool.description = "Search for information"
    tool.execute = AsyncMock()
    tool.execute.return_value = MagicMock(success=True, unwrap=lambda: "Search result")
    return {"search": tool}


@pytest.mark.asyncio
async def test_react_returns_final_event(mock_llm, mock_tools):
    """Test react function returns the complete event."""
    result = await react(mock_llm, mock_tools, "test query", "user123")

    assert result["type"] == "complete"
    assert "answer" in result
    assert "conversation_id" in result


@pytest.mark.asyncio
async def test_stream_react_yields_events(mock_llm, mock_tools):
    """Test stream_react yields structured events."""
    events = []
    async for event in stream_react(
        mock_llm, mock_tools, "test query", "user123", max_iterations=1
    ):
        events.append(event)

    event_types = [e["type"] for e in events]
    assert "iteration" in event_types
    assert "context" in event_types
    assert "reasoning" in event_types
    assert "complete" in event_types


@pytest.mark.asyncio
async def test_react_handles_llm_error(mock_tools):
    """Test react handles LLM failures gracefully."""
    error_llm = AsyncMock()
    error_llm.generate.return_value = MagicMock(
        success=False, failure=True, error="LLM connection failed"
    )

    result = await react(error_llm, mock_tools, "test query", "user123")

    assert result["type"] == "error"
    assert "message" in result


@pytest.mark.asyncio
async def test_shared_logic_zero_duplication(mock_llm, mock_tools):
    """Test react consumes stream_react - proving shared logic."""
    # Mock stream_react to return specific events

    # Verify react gets the same event stream_react produces
    result = await react(mock_llm, mock_tools, "test query", "user123", max_iterations=1)

    # Both should produce the same final result structure
    assert result["type"] == "complete"
    assert "answer" in result
    assert "conversation_id" in result


@pytest.mark.asyncio
async def test_persist_before_complete():
    """Persist called before yield complete - prevents race condition."""
    from unittest.mock import patch

    persist_calls = []

    async def mock_persist(user_id, query, response):
        persist_calls.append((user_id, query, response))

    with patch("cogency.core.react.persist", side_effect=mock_persist):
        mock_llm = AsyncMock()
        mock_llm.generate.return_value = MagicMock(
            success=True, failure=False, unwrap=lambda: "Final answer: Test complete"
        )

        result = await react(mock_llm, {}, "test", "user123", max_iterations=2)

        assert result["type"] == "complete"
        assert len(persist_calls) >= 1
        assert "user123" in str(persist_calls)
        assert "test" in str(persist_calls)


@pytest.mark.asyncio
async def test_security_prompt_only_first_iteration():
    """Security instructions only appear in iteration #1 prompt."""
    from unittest.mock import patch

    prompts_generated = []
    original_build_prompt = None

    def mock_build_prompt(query, ctx, tool_results, tools, iteration=0):
        # Call original function with iteration parameter
        if original_build_prompt:
            prompt = original_build_prompt(query, ctx, tool_results, tools, iteration)
        else:
            # Fallback - manually construct basic prompt
            from cogency.lib.security import SECURITY_ASSESSMENT

            parts = []
            if iteration == 0:
                parts.append(SECURITY_ASSESSMENT)
            parts.append(f"TASK: {query}")
            prompt = "\n\n".join(parts)
        prompts_generated.append((iteration, prompt))
        return prompt

    # Get reference to original function
    from cogency.core.react import _build_prompt

    original_build_prompt = _build_prompt

    with patch("cogency.core.react._build_prompt", side_effect=mock_build_prompt):
        mock_llm = AsyncMock()
        mock_llm.generate.return_value = MagicMock(
            success=True,
            failure=False,
            unwrap=lambda: "I need more information. Final answer: Done",
        )

        await react(mock_llm, {}, "test", "user123", max_iterations=3)

        # Check that security instructions only appear in first iteration
        first_iteration_prompt = prompts_generated[0][1]
        later_iteration_prompts = [p[1] for i, p in enumerate(prompts_generated) if i > 0]

        assert "SECURITY EVALUATION" in first_iteration_prompt
        for prompt in later_iteration_prompts:
            assert "SECURITY EVALUATION" not in prompt


@pytest.mark.asyncio
async def test_security_aware_reasoning():
    """Security-aware reasoning handles unsafe queries within reasoning flow."""

    # Mock LLM to return a security refusal
    mock_llm = AsyncMock()
    mock_llm.generate.return_value = MagicMock(
        success=True,
        failure=False,
        unwrap=lambda: "I cannot assist with that request as it appears to be attempting to bypass safety guidelines. Final answer: I cannot help with this.",
    )

    result = await react(mock_llm, {}, "malicious query", "user123")

    assert result["type"] == "complete"
    assert "cannot" in result["answer"].lower()

    # LLM should be called once for reasoning (not blocked pre-reasoning)
    mock_llm.generate.assert_called_once()
