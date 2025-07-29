"""Config tests."""

import pytest

from cogency.config import Observe, Persist, Robust, setup_config


def test_robust_defaults():
    config = Robust()

    assert config.retry is True
    assert config.circuit is True
    assert config.rate_limit is True
    assert config.checkpoint is True
    assert config.attempts == 3
    assert config.backoff == "exponential"
    assert config.backoff_delay == 0.1
    assert config.backoff_factor == 2.0
    assert config.backoff_max == 30.0


def test_robust_custom():
    config = Robust(retry=False, attempts=5, backoff="linear", backoff_delay=0.5)

    assert config.retry is False
    assert config.attempts == 5
    assert config.backoff == "linear"
    assert config.backoff_delay == 0.5


def test_observe_defaults():
    config = Observe()

    assert config.metrics is True
    assert config.timing is True
    assert config.counters is True
    assert config.phases is None
    assert config.export_format == "prometheus"
    assert config.export_endpoint is None


def test_observe_custom():
    config = Observe(metrics=False, timing=False, phases=["reason", "act"], export_format="json")

    assert config.metrics is False
    assert config.timing is False
    assert config.phases == ["reason", "act"]
    assert config.export_format == "json"


def test_persist_defaults():
    config = Persist()

    assert config.enabled is True
    assert config.store is None


def test_persist_custom():
    mock_store = "filesystem_store"
    config = Persist(enabled=False, store=mock_store)

    assert config.enabled is False
    assert config.store == mock_store


def test_setup_config_false():
    result = setup_config(Robust, False)
    assert result is None


def test_setup_config_true():
    result = setup_config(Robust, True)
    assert isinstance(result, Robust)
    assert result.retry is True


def test_setup_config_instance():
    custom_config = Robust(attempts=10)
    result = setup_config(Robust, custom_config)
    assert result is custom_config
    assert result.attempts == 10


def test_setup_config_with_store():
    mock_store = "test_store"
    result = setup_config(Persist, mock_store, store=mock_store)
    assert isinstance(result, Persist)
    assert result.store == mock_store


def test_setup_config_none():
    result = setup_config(Robust, None)
    assert result is None
