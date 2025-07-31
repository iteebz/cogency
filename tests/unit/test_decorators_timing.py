"""Test decorator timing consolidation."""

import pytest

from cogency.config import ObserveConfig
from cogency.decorators import PhaseConfig, create_phase_decorators, elapsed


@pytest.mark.asyncio
async def test_phase_timer_injection():
    """Test that decorator injects timer context."""
    config = PhaseConfig(observe=ObserveConfig())
    phase_decorators = create_phase_decorators(config)

    @phase_decorators.generic()
    async def test_phase(**kwargs):
        # Should have timer context injected
        duration = elapsed(**kwargs)
        assert duration >= 0.0
        return "result"

    result = await test_phase()
    assert result == "result"


@pytest.mark.asyncio
async def test_no_observe_passthrough():
    """Test that without observe config, no timer injection occurs."""
    config = PhaseConfig(observe=None)
    phase_decorators = create_phase_decorators(config)

    @phase_decorators.generic()
    async def test_phase(**kwargs):
        # Should not have timer context
        duration = elapsed(**kwargs)
        assert duration == 0.0
        return "result"

    result = await test_phase()
    assert result == "result"
