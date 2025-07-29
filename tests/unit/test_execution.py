"""Execution tests."""

from unittest.mock import AsyncMock

import pytest

from cogency.execution import run_agent
from cogency.state import State


@pytest.mark.asyncio
async def test_direct_response():
    state = State("test query", user_id="user", depth=5)
    state.respond_directly = True
    
    preprocess = AsyncMock()
    reason = AsyncMock()
    act = AsyncMock()
    respond = AsyncMock()
    notify = AsyncMock()
    
    await run_agent(state, preprocess, reason, act, respond, notify)
    
    preprocess.assert_called_once()
    reason.assert_not_called()
    act.assert_not_called()
    respond.assert_called_once()


@pytest.mark.asyncio
async def test_react_loop():
    state = State("test query", user_id="user", depth=5)
    state.respond_directly = False
    state.tool_calls = ["tool1"]  # First iteration has tools
    
    preprocess = AsyncMock()
    reason = AsyncMock()
    act = AsyncMock()
    respond = AsyncMock()
    notify = AsyncMock()
    
    # Mock clearing tools on second reason call
    async def maybe_clear_tools(*args):
        if reason.call_count == 2:
            state.tool_calls = []
    
    reason.side_effect = maybe_clear_tools
    
    await run_agent(state, preprocess, reason, act, respond, notify)
    
    preprocess.assert_called_once()
    assert reason.call_count >= 1  # Called at least once
    assert act.call_count >= 1   # Called at least once
    respond.assert_called_once()
    assert state.iteration >= 1


@pytest.mark.asyncio
async def test_depth_limit():
    state = State("test query", user_id="user", depth=2)
    state.respond_directly = False
    state.tool_calls = ["tool1"]  # Always has tools (infinite loop scenario)
    
    preprocess = AsyncMock()
    reason = AsyncMock()
    act = AsyncMock()
    respond = AsyncMock()
    notify = AsyncMock()
    
    await run_agent(state, preprocess, reason, act, respond, notify)
    
    preprocess.assert_called_once()
    assert reason.call_count == 2  # Called up to depth limit
    assert act.call_count == 2
    respond.assert_called_once()
    assert state.iteration == 2


@pytest.mark.asyncio
async def test_stop_reason():
    state = State("test query", user_id="user", depth=5)
    state.respond_directly = False
    state.tool_calls = ["tool1"]
    
    preprocess = AsyncMock()
    reason = AsyncMock()
    act = AsyncMock()
    respond = AsyncMock()
    notify = AsyncMock()
    
    # Mock setting stop reason
    async def set_stop(*args):
        state.stop_reason = "user_requested"
    
    act.side_effect = set_stop
    
    await run_agent(state, preprocess, reason, act, respond, notify)
    
    preprocess.assert_called_once()
    reason.assert_called_once()
    act.assert_called_once()
    respond.assert_called_once()
    assert state.iteration == 1


@pytest.mark.asyncio
async def test_no_notify():
    state = State("test query", user_id="user", depth=5)
    state.respond_directly = True
    
    preprocess = AsyncMock()
    reason = AsyncMock()
    act = AsyncMock()
    respond = AsyncMock()
    
    await run_agent(state, preprocess, reason, act, respond)
    
    preprocess.assert_called_once_with(state, None)
    respond.assert_called_once_with(state, None)