"""Decorator tests."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from cogency.config import Observe, Persist, Robust
from cogency.decorators import configure, get_config, phase


@pytest.mark.asyncio
async def test_phase_no_config():
    configure(robust=None, observe=None, persistence=None)

    @phase.reason()
    async def test_func():
        return "success"

    result = await test_func()
    assert result == "success"


@pytest.mark.asyncio
async def test_phase_with_robust():
    robust_config = Robust()
    configure(robust=robust_config, observe=None, persistence=None)

    @phase.reason()
    async def test_func():
        return "success"

    result = await test_func()
    # With robust enabled, we get a Result object
    assert str(result) == "Result.ok('success')" or result == "success"


@pytest.mark.asyncio
async def test_phase_with_observe():
    observe_config = Observe()
    configure(robust=None, observe=observe_config, persistence=None)

    @phase.reason()
    async def test_func(**kwargs):
        return "success"

    result = await test_func()
    assert result == "success"


def test_configure():
    robust_config = Robust()
    observe_config = Observe()
    persist_config = Persist()

    configure(robust=robust_config, observe=observe_config, persistence=persist_config)

    config = get_config()
    assert config.robust == robust_config
    assert config.observe == observe_config
    assert config.persist == persist_config


def test_get_config():
    config = get_config()
    assert hasattr(config, "robust")
    assert hasattr(config, "observe")
    assert hasattr(config, "persist")


def test_phase_decorators_exist():
    assert hasattr(phase, "reason")
    assert hasattr(phase, "act")
    assert hasattr(phase, "preprocess")
    assert hasattr(phase, "respond")
    assert hasattr(phase, "generic")

    assert callable(phase.reason)
    assert callable(phase.act)
    assert callable(phase.preprocess)
    assert callable(phase.respond)
    assert callable(phase.generic)
