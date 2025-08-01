"""Decorator tests."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from cogency.config import ObserveConfig, PersistConfig, RobustConfig
from cogency.decorators import StepConfig, phase, step_decorators


@pytest.mark.asyncio
async def test_step_no_config():
    """Test phase decorators with no config."""

    @phase.reason()
    async def test_func():
        return "success"

    result = await test_func()
    assert result == "success"


@pytest.mark.asyncio
async def test_step_with_robust():
    """Test phase decorators with robust config."""
    robust_config = RobustConfig()
    config = StepConfig(robust=robust_config)
    phase_with_config = step_decorators(config)

    @phase_with_config.reason()
    async def test_func():
        return "success"

    result = await test_func()
    # With robust enabled, we get a Result object
    assert str(result) == "Result.ok('success')" or result == "success"


@pytest.mark.asyncio
async def test_step_with_observe():
    """Test phase decorators with observe config."""
    observe_config = ObserveConfig()
    config = StepConfig(observe=observe_config)
    phase_with_config = step_decorators(config)

    @phase_with_config.reason()
    async def test_func(**kwargs):
        return "success"

    result = await test_func()
    assert result == "success"


def test_step_config():
    """Test StepConfig and step_decorators."""
    robust_config = RobustConfig()
    observe_config = ObserveConfig()
    persist_config = PersistConfig()

    config = StepConfig(robust=robust_config, observe=observe_config, persist=persist_config)
    assert config.robust == robust_config
    assert config.observe == observe_config
    assert config.persist == persist_config

    # Test creating decorators with config
    phase_decorators = step_decorators(config)
    assert hasattr(phase_decorators, "reason")
    assert hasattr(phase_decorators, "act")
    assert callable(phase_decorators.reason)


def test_step_decorators_exist():
    assert hasattr(phase, "reason")
    assert hasattr(phase, "act")
    assert hasattr(phase, "prepare")
    assert hasattr(phase, "respond")
    assert hasattr(phase, "generic")

    assert callable(phase.reason)
    assert callable(phase.act)
    assert callable(phase.prepare)
    assert callable(phase.respond)
    assert callable(phase.generic)
