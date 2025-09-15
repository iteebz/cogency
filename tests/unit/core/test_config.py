"""Immutable configuration validation tests."""

from unittest.mock import Mock

import pytest

from cogency.core.config import Config


def test_config(mock_llm):
    """Config is immutable, handles tools/flags, validates modes."""
    mock_storage = Mock()
    mock_tool = Mock()
    mock_tool.name = "test_tool"

    # Immutability
    config = Config(llm=mock_llm, storage=mock_storage, tools=[mock_tool])
    with pytest.raises(AttributeError):
        config.mode = "different"

    # Defaults
    assert config.max_iterations == 10
    assert config.mode == "auto"
    assert config.profile is True
    assert config.sandbox is True

    # Custom values + tools
    config = Config(
        llm=mock_llm,
        storage=mock_storage,
        tools=[mock_tool],
        max_iterations=5,
        mode="replay",
        profile=False,
        sandbox=False,
    )
    assert config.llm is mock_llm
    assert len(config.tools) == 1
    assert config.tools[0].name == "test_tool"
    assert config.max_iterations == 5
    assert config.mode == "replay"
    assert config.profile is False
    assert config.sandbox is False
