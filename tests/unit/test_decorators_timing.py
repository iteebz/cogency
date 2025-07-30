"""Test decorator timing consolidation."""

import pytest

from cogency.config import ObserveConfig
from cogency.decorators import configure, elapsed, phase


@pytest.mark.asyncio
async def test_phase_timer_injection():
    """Test that decorator injects timer context."""
    configure(observe=ObserveConfig())

    @phase.generic()
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
    configure(observe=None)

    @phase.generic()
    async def test_phase(**kwargs):
        # Should not have timer context
        duration = elapsed(**kwargs)
        assert duration == 0.0
        return "result"

    result = await test_phase()
    assert result == "result"
