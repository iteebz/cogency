"""Pragmatic tests for recovery business logic."""

import pytest
from resilient_result import Result

from cogency.robust.recovery import Recovery
from cogency.state import State


@pytest.mark.asyncio
async def test_preprocess_memory_fail():
    """Memory failure disables memory."""
    state = State("test query")
    state.memory_enabled = True
    error = Result.fail({"memory_failed": True})
    
    result = await Recovery.recover(error, state, "preprocess")
    
    assert result.success
    assert not state.memory_enabled
    assert result.data["recovery"] == "disable_memory"


@pytest.mark.asyncio
async def test_reasoning_loop_recovery():
    """Loop detection forces response."""
    state = State("test query")
    error = Result.fail({"loop_detected": True})
    
    result = await Recovery.recover(error, state, "reasoning")
    
    assert result.success
    assert state.next_phase == "respond"
    assert state.stop_reason == "loop_recovery"


@pytest.mark.asyncio
async def test_reasoning_mode_fallback():
    """Deep mode falls back to fast."""
    state = State("test query")
    state.mode = "deep"
    error = Result.fail({"mode": "deep"})
    
    result = await Recovery.recover(error, state, "reasoning")
    
    assert result.success
    assert state.mode == "fast"
    assert result.data["recovery"] == "fallback_to_fast"


@pytest.mark.asyncio
async def test_action_nonrecoverable():
    """Non-recoverable actions force response."""
    state = State("test query")
    error = Result.fail({"recoverable": False})
    
    result = await Recovery.recover(error, state, "action")
    
    assert result.success
    assert state.next_phase == "respond"
    assert state.stop_reason == "non_recoverable_action_error"


@pytest.mark.asyncio
async def test_action_retry():
    """Recoverable actions retry reasoning."""
    state = State("test query")
    error = Result.fail({"failed_tools": ["bash"], "message": "command failed"})
    
    result = await Recovery.recover(error, state, "action")
    
    assert result.success
    assert state.next_phase == "reason"
    assert state.execution_results["type"] == "error"
    assert "bash" in state.execution_results["failed_tools"]


@pytest.mark.asyncio
async def test_response_fallback():
    """Response fallback sets error message."""
    state = State("test query")
    error = Result.fail({"message": "generation failed"})
    
    result = await Recovery.recover(error, state, "response")
    
    assert result.success
    assert "generation failed" in state.response


@pytest.mark.asyncio
async def test_string_error_normalization():
    """String errors get normalized to dict."""
    state = State("test query")
    error = Result.fail("simple error message")
    
    result = await Recovery.recover(error, state, "preprocess")
    
    assert result.success
    assert result.data["recovery"] == "skip_enrichment"