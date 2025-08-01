"""Test decorator timing consolidation."""

import pytest

from cogency.config import ObserveConfig
from cogency.decorators import StepConfig, elapsed, step_decorators


@pytest.mark.asyncio
async def test_step_timer_injection():
    """Test that decorator injects timer context."""
    config = StepConfig(observe=ObserveConfig())
    phase_decorators = step_decorators(config)

    @phase_decorators.generic()
    async def test_step(**kwargs):
        # Should have timer context injected
        duration = elapsed(**kwargs)
        assert duration >= 0.0
        return "result"

    result = await test_step()
    assert result == "result"


@pytest.mark.asyncio
async def test_no_observe_passthrough():
    """Test that without observe config, no timer injection occurs."""
    config = StepConfig(observe=None)
    phase_decorators = step_decorators(config)

    @phase_decorators.generic()
    async def test_step(**kwargs):
        # Should not have timer context
        duration = elapsed(**kwargs)
        assert duration == 0.0
        return "result"

    result = await test_step()
    assert result == "result"
