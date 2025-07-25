"""Test Cogency domain-specific resilience decorators."""

from unittest.mock import Mock

import pytest

from cogency.resilience import safe


@pytest.mark.asyncio
async def test_safe_act_decorator():
    """Test @safe.act() for tool execution resilience."""

    @safe.act(retries=2, unwrap_state=False)
    async def mock_tool_execution():
        if not hasattr(mock_tool_execution, "call_count"):
            mock_tool_execution.call_count = 0
        mock_tool_execution.call_count += 1

        if mock_tool_execution.call_count == 1:
            raise Exception("network timeout")
        return "tool executed"

    result = await mock_tool_execution()
    assert result.success
    assert result.data == "tool executed"
    assert mock_tool_execution.call_count == 2


@pytest.mark.asyncio
async def test_safe_memory_decorator():
    """Test @safe.memory() for memory operation resilience."""

    @safe.memory(retries=2, unwrap_state=False)
    async def mock_memory_store():
        if not hasattr(mock_memory_store, "call_count"):
            mock_memory_store.call_count = 0
        mock_memory_store.call_count += 1

        if mock_memory_store.call_count == 1:
            raise Exception("database timeout")
        return "stored"

    result = await mock_memory_store()
    assert result.success
    assert result.data == "stored"


@pytest.mark.asyncio
async def test_safe_reasoning_fallback():
    """Test @safe.reasoning() mode fallback behavior."""

    # Mock state object with react_mode
    state = Mock()
    state.react_mode = "deep"

    @safe.reasoning(retries=2, unwrap_state=False)
    async def mock_llm_reasoning(state_obj):
        if state_obj.react_mode == "deep":
            # First call should trigger fallback to fast mode
            raise Exception("deep mode timeout")
        return f"reasoning complete in {state_obj.react_mode} mode"

    result = await mock_llm_reasoning(state)
    assert result.success
    assert result.data == "reasoning complete in fast mode"
    assert state.react_mode == "fast"  # Should have been changed by recovery


@pytest.mark.asyncio
async def test_safe_reasoning_no_fallback():
    """Test @safe.reasoning() when no fallback available."""

    @safe.reasoning(retries=1, unwrap_state=False)
    async def mock_llm_reasoning():
        raise Exception("reasoning error")

    result = await mock_llm_reasoning()
    assert not result.success
    assert "reasoning error" in str(result.error)
