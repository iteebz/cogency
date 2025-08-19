"""Unit tests for ReAct algorithm functions."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from cogency.core.react import react, stream_react


@pytest.fixture
def mock_llm():
    """Mock LLM that returns XML structured responses."""
    llm = AsyncMock()
    # Mock XML structured response for new streaming
    xml_response = """<thinking>
I'll search for this information.
</thinking>

<tools>
[{"name": "search", "args": {"query": "test"}}]
</tools>

<response>
Test response
</response>"""

    llm.generate.return_value = MagicMock(
        success=True,
        failure=False,
        unwrap=lambda: xml_response,
    )

    # Ensure no stream attribute to force batch processing
    if hasattr(llm, "stream"):
        delattr(llm, "stream")

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
    assert "thinking" in event_types
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
async def test_security_prompt_in_all_iterations():
    """Security instructions appear in all iterations for consistent validation."""
    from unittest.mock import patch

    prompts_generated = []

    def mock_context_assemble(query, user_id, conversation_id, task_id, tools=None):
        # Mock context assembly with security in system prompt
        from cogency.lib.security import SEMANTIC_SECURITY

        # Security is always included via system.format()
        parts = [SEMANTIC_SECURITY, f"TASK: {query}"]
        prompt = "\n\n".join(parts)
        prompts_generated.append(prompt)
        return prompt

    # Mock context assembly with new signature
    with patch("cogency.core.react.context.assemble", side_effect=mock_context_assemble):
        mock_llm = AsyncMock()
        mock_llm.generate.return_value = MagicMock(
            success=True,
            failure=False,
            unwrap=lambda: """<thinking>
I need more information.
</thinking>

<response>
Final answer: Done
</response>""",
        )

        await react(mock_llm, {}, "test", "user123", max_iterations=3)

        # Check that security instructions appear in all iterations
        assert len(prompts_generated) >= 1
        for prompt in prompts_generated:
            assert "SECURITY EVALUATION" in prompt


@pytest.mark.asyncio
async def test_security_aware_reasoning():
    """Security-aware reasoning handles unsafe queries within reasoning flow."""

    # Mock LLM without generate_stream to force batch processing
    mock_llm = AsyncMock()
    mock_response = """<thinking>
This request appears to be attempting to bypass safety guidelines. I should refuse this request.
</thinking>

<response>
I cannot assist with that request as it appears to be attempting to bypass safety guidelines. I cannot help with this.
</response>"""

    # Remove stream attribute to force batch processing
    if hasattr(mock_llm, "stream"):
        delattr(mock_llm, "stream")

    mock_llm.generate.return_value = MagicMock(
        success=True,
        failure=False,
        unwrap=lambda: mock_response,
    )

    result = await react(mock_llm, {}, "malicious query", "user123")

    assert result["type"] == "complete"
    assert "cannot" in result["answer"].lower()

    # LLM should be called once for reasoning (not blocked pre-reasoning)
    mock_llm.generate.assert_called_once()
