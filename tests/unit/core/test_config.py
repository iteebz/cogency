"""Config tests - Immutable behavior flag validation."""

from unittest.mock import MagicMock

import pytest

from cogency.core.config import Config


def test_config_immutable(mock_llm, mock_storage):
    """Config is immutable - no ceremony modifications."""
    mock_tool = MagicMock()
    mock_tool.name = "test"

    config = Config(llm=mock_llm, storage=mock_storage, tools=[mock_tool])

    # Should be frozen
    with pytest.raises(AttributeError):  # frozen dataclass
        config.mode = "different"

    # Should have defaults
    assert config.max_iterations == 3
    assert config.mode == "auto"
    assert config.profile is True
    assert config.sandbox is True


def test_config_behavior_flags(mock_llm, mock_storage):
    """Config behavior flags control subsystems."""

    # Test profile flag
    config_profile_on = Config(llm=mock_llm, storage=mock_storage, tools=[], profile=True)
    config_profile_off = Config(llm=mock_llm, storage=mock_storage, tools=[], profile=False)

    assert config_profile_on.profile is True
    assert config_profile_off.profile is False

    # Test sandbox flag
    config_sandbox_on = Config(llm=mock_llm, storage=mock_storage, tools=[], sandbox=True)
    config_sandbox_off = Config(llm=mock_llm, storage=mock_storage, tools=[], sandbox=False)

    assert config_sandbox_on.sandbox is True
    assert config_sandbox_off.sandbox is False


def test_config_mode_validation(mock_llm, mock_storage):
    """Config mode should validate against mental model."""

    # Valid modes from mental model
    valid_modes = ["auto", "replay", "resume"]

    for mode in valid_modes:
        config = Config(llm=mock_llm, storage=mock_storage, tools=[], mode=mode)
        assert config.mode == mode

    # Invalid modes should be rejected (but Config doesn't validate yet)
    # This test documents expected behavior
    config = Config(llm=mock_llm, storage=mock_storage, tools=[], mode="invalid")
    assert config.mode == "invalid"  # Currently allows any string


def test_config_required_fields(mock_llm, mock_storage):
    """Config requires LLM and tools - no defaults for core capabilities."""

    # Should require both LLM and tools
    config = Config(llm=mock_llm, storage=mock_storage, tools=[])
    assert config.llm is mock_llm
    assert config.tools == []

    # Test with actual tools
    mock_tool = MagicMock()
    mock_tool.name = "test_tool"
    config_with_tools = Config(llm=mock_llm, storage=mock_storage, tools=[mock_tool])
    assert len(config_with_tools.tools) == 1


def test_config_canonical_separation(mock_llm, mock_storage):
    """Config separates capabilities from runtime params."""

    config = Config(
        llm=mock_llm,
        storage=mock_storage,
        tools=[],
        max_iterations=3,
        mode="replay",
        profile=False,
        sandbox=False,
    )

    # Capabilities - what agent CAN do
    assert config.llm is not None
    assert isinstance(config.tools, list)

    # Behavior flags - HOW agent behaves
    assert config.max_iterations == 3
    assert config.mode == "replay"
    assert config.profile is False
    assert config.sandbox is False

    # Runtime params (user_id, conversation_id, query) NOT in config
    assert not hasattr(config, "user_id")
    assert not hasattr(config, "conversation_id")
    assert not hasattr(config, "query")
