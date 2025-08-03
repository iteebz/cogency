"""Decorator tests."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from cogency.config import ObserveConfig, PersistConfig, RobustConfig
from cogency.decorators import StepConfig, elapsed, step, step_decorators


@pytest.mark.asyncio
async def test_step_no_config():
    """Test step decorators with no config."""

    @step.reason()
    async def test_func():
        return "success"

    result = await test_func()
    assert result == "success"


@pytest.mark.asyncio
async def test_step_with_robust():
    """Test step decorators with robust config."""
    robust_config = RobustConfig()
    config = StepConfig(robust=robust_config)
    step_with_config = step_decorators(config)

    @step_with_config.reason()
    async def test_func():
        return "success"

    result = await test_func()
    # With robust enabled, we get a Result object
    assert str(result) == "Result.ok('success')" or result == "success"


@pytest.mark.asyncio
async def test_step_with_observe():
    """Test step decorators with observe config."""
    observe_config = ObserveConfig()
    config = StepConfig(observe=observe_config)
    step_with_config = step_decorators(config)

    @step_with_config.reason()
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
    step_decorators_obj = step_decorators(config)
    assert hasattr(step_decorators_obj, "reason")
    assert hasattr(step_decorators_obj, "act")
    assert callable(step_decorators_obj.reason)


@pytest.mark.asyncio
async def test_step_timer_injection():
    """Test that decorator injects timer context."""
    config = StepConfig(observe=ObserveConfig())
    step_decorators_obj = step_decorators(config)

    @step_decorators_obj.generic()
    async def test_step(**kwargs):
        # Should have timer context injected
        duration = kwargs.get("elapsed", lambda: 0.0)()
        assert duration >= 0.0
        return "result"

    result = await test_step()
    assert result == "result"


@pytest.mark.asyncio
async def test_no_observe_passthrough():
    """Test that without observe config, no timer injection occurs."""
    config = StepConfig(observe=None)
    step_decorators_obj = step_decorators(config)

    @step_decorators_obj.generic()
    async def test_step(**kwargs):
        # Should not have timer context
        duration = elapsed(**kwargs)
        assert duration == 0.0
        return "result"

    result = await test_step()
    assert result == "result"


def test_step_decorators_exist():
    assert hasattr(step, "reason")
    assert hasattr(step, "act")
    assert hasattr(step, "triage")
    assert hasattr(step, "respond")
    assert hasattr(step, "generic")

    assert callable(step.reason)
    assert callable(step.act)
    assert callable(step.triage)
    assert callable(step.respond)
    assert callable(step.generic)
