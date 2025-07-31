"""Execution tests for early return architecture."""

from unittest.mock import AsyncMock

import pytest

from cogency.execution import run_agent
from cogency.state import State


@pytest.mark.asyncio
async def test_early_response_from_preprocess():
    """Test early return from preprocess phase."""
    state = State("test query", user_id="user", depth=5)

    preprocess = AsyncMock(return_value="Early response")
    reason = AsyncMock()
    act = AsyncMock()
    respond = AsyncMock()
    notify = AsyncMock()

    await run_agent(state, preprocess, reason, act, respond, notify)

    preprocess.assert_called_once()
    reason.assert_not_called()
    act.assert_not_called()
    respond.assert_not_called()
    assert state.response == "Early response"


@pytest.mark.asyncio
async def test_early_response_from_reason():
    """Test early return from reason phase."""
    state = State("test query", user_id="user", depth=5)

    preprocess = AsyncMock(return_value=None)
    reason = AsyncMock(return_value="Reasoning response")
    act = AsyncMock()
    respond = AsyncMock()
    notify = AsyncMock()

    await run_agent(state, preprocess, reason, act, respond, notify)

    preprocess.assert_called_once()
    reason.assert_called_once()
    act.assert_not_called()
    respond.assert_not_called()
    assert state.response == "Reasoning response"


@pytest.mark.asyncio
async def test_react_loop_without_early_return():
    """Test full ReAct loop when no early returns occur."""
    state = State("test query", user_id="user", depth=5)
    state.tool_calls = ["tool1"]  # First iteration has tools

    preprocess = AsyncMock(return_value=None)
    reason = AsyncMock(return_value=None)
    act = AsyncMock(return_value=None)
    respond = AsyncMock()
    notify = AsyncMock()

    # Mock clearing tools on second reason call
    async def maybe_clear_tools(*args):
        if reason.call_count == 2:
            state.tool_calls = []
        return None

    reason.side_effect = maybe_clear_tools

    await run_agent(state, preprocess, reason, act, respond, notify)

    preprocess.assert_called_once()
    assert reason.call_count >= 1  # Called at least once
    assert act.call_count >= 1  # Called at least once
    respond.assert_called_once()
    assert state.iteration >= 1


@pytest.mark.asyncio
async def test_depth_limit():
    """Test depth limit with no early returns."""
    state = State("test query", user_id="user", depth=2)
    state.tool_calls = ["tool1"]  # Always has tools (infinite loop scenario)

    preprocess = AsyncMock(return_value=None)
    reason = AsyncMock(return_value=None)
    act = AsyncMock(return_value=None)
    respond = AsyncMock()
    notify = AsyncMock()

    await run_agent(state, preprocess, reason, act, respond, notify)

    preprocess.assert_called_once()
    assert reason.call_count == 2  # Called up to depth limit
    assert act.call_count == 2
    respond.assert_called_once()
    assert state.iteration == 2


@pytest.mark.asyncio
async def test_early_return_from_act():
    """Test early return from act phase."""
    state = State("test query", user_id="user", depth=5)
    state.tool_calls = ["tool1"]

    preprocess = AsyncMock(return_value=None)
    reason = AsyncMock(return_value=None)
    act = AsyncMock(return_value="Act response")
    respond = AsyncMock()
    notify = AsyncMock()

    await run_agent(state, preprocess, reason, act, respond, notify)

    preprocess.assert_called_once()
    reason.assert_called_once()
    act.assert_called_once()
    respond.assert_not_called()
    assert state.response == "Act response"


@pytest.mark.asyncio
async def test_no_notify():
    """Test execution without notifier."""
    state = State("test query", user_id="user", depth=5)

    preprocess = AsyncMock(return_value="Early response")
    reason = AsyncMock()
    act = AsyncMock()
    respond = AsyncMock()

    await run_agent(state, preprocess, reason, act, respond)

    preprocess.assert_called_once_with(state, None)
    assert state.response == "Early response"
