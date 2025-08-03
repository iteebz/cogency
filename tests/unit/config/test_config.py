"""Config tests."""

import pytest

from cogency.config import ObserveConfig, PersistConfig, RobustConfig
from cogency.config.dataclasses import _setup_config


def test_robust_defaults():
    config = RobustConfig()

    assert config.retry is False
    assert config.circuit is True
    assert config.rate_limit is True
    assert config.checkpoint is True
    assert config.attempts == 3
    assert config.backoff == "exponential"
    assert config.backoff_delay == 0.1
    assert config.backoff_factor == 2.0
    assert config.backoff_max == 30.0


def test_robust_custom():
    config = RobustConfig(retry=False, attempts=5, backoff="linear", backoff_delay=0.5)

    assert config.retry is False
    assert config.attempts == 5
    assert config.backoff == "linear"
    assert config.backoff_delay == 0.5


def test_observe_defaults():
    config = ObserveConfig()

    assert config.metrics is True
    assert config.timing is True
    assert config.counters is True
    assert config.steps is None
    assert config.export_format == "prometheus"
    assert config.export_endpoint is None


def test_observe_custom():
    config = ObserveConfig(
        metrics=False, timing=False, steps=["reason", "act"], export_format="json"
    )

    assert config.metrics is False
    assert config.timing is False
    assert config.steps == ["reason", "act"]
    assert config.export_format == "json"


def test_persist_defaults():
    config = PersistConfig()

    assert config.enabled is True
    assert config.store is None


def test_persist_custom():
    mock_store = "filesystem_store"
    config = PersistConfig(enabled=False, store=mock_store)

    assert config.enabled is False
    assert config.store == mock_store


def test__setup_config_false():
    result = _setup_config(RobustConfig, False)
    assert result is None


def test__setup_config_true():
    result = _setup_config(RobustConfig, True)
    assert isinstance(result, RobustConfig)
    assert result.retry is False


def test__setup_config_instance():
    custom_config = RobustConfig(attempts=10)
    result = _setup_config(RobustConfig, custom_config)
    assert result is custom_config
    assert result.attempts == 10


def test__setup_config_with_store():
    mock_store = "test_store"
    result = _setup_config(PersistConfig, mock_store, store=mock_store)
    assert isinstance(result, PersistConfig)
    assert result.store == mock_store


def test__setup_config_none():
    result = _setup_config(RobustConfig, None)
    assert result is None
