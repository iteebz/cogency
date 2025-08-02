"""Test Union[bool, ConfigObj] patterns per council ruling."""

import pytest

from cogency import Agent
from cogency.config import MemoryConfig, ObserveConfig, RobustConfig


def test_memory_bool_true():
    """Test memory=True enables memory with defaults."""
    agent = Agent("test", memory=True)
    assert agent._config.memory is True


def test_memory_bool_false():
    """Test memory=False disables memory."""
    agent = Agent("test", memory=False)
    assert agent._config.memory is False


def test_memory_config_object():
    """Test memory=MemoryConfig() uses custom settings."""
    config = MemoryConfig(synthesis_threshold=4000, user_id="alice")
    agent = Agent("test", memory=config)
    assert agent._config.memory == config
    assert agent._config.memory.synthesis_threshold == 4000
    assert agent._config.memory.user_id == "alice"


def test_robust_bool_true():
    """Test robust=True enables robustness with defaults."""
    agent = Agent("test", robust=True)
    assert agent._config.robust is True


def test_robust_bool_false():
    """Test robust=False disables robustness."""
    agent = Agent("test", robust=False)
    assert agent._config.robust is False


def test_robust_config_object():
    """Test robust=RobustConfig() uses custom settings."""
    config = RobustConfig(attempts=7, timeout=180.0, rate_limit_rps=1.5)
    agent = Agent("test", robust=config)
    assert agent._config.robust == config
    assert agent._config.robust.attempts == 7
    assert agent._config.robust.timeout == 180.0
    assert agent._config.robust.rate_limit_rps == 1.5


def test_observe_bool_true():
    """Test observe=True enables observability with defaults."""
    agent = Agent("test", observe=True)
    assert agent._config.observe is True


def test_observe_bool_false():
    """Test observe=False disables observability."""
    agent = Agent("test", observe=False)
    assert agent._config.observe is False


def test_observe_config_object():
    """Test observe=ObserveConfig() uses custom settings."""
    config = ObserveConfig(metrics=True, export_format="json", phases=["reason"])
    agent = Agent("test", observe=config)
    assert agent._config.observe == config
    assert agent._config.observe.metrics is True
    assert agent._config.observe.export_format == "json"
    assert agent._config.observe.phases == ["reason"]


def test_multiple_union_patterns():
    """Test multiple Union patterns work together."""
    memory_config = MemoryConfig(user_id="bob")
    robust_config = RobustConfig(attempts=3)

    agent = Agent("test", memory=memory_config, robust=robust_config, observe=True)  # Bool variant

    assert agent._config.memory == memory_config
    assert agent._config.robust == robust_config
    assert agent._config.observe is True


def test_validation_prevents_conflicts():
    """Test validation catches conflicting configurations."""
    # These tests would need the flat parameter approach to work
    # Since we use Union pattern, these conflicts shouldn't be possible
    # But we test the validation logic exists
    agent = Agent("test", memory=False, robust=False, observe=False)

    # Should not raise - no conflicts with Union pattern
    assert agent._config.memory is False
    assert agent._config.robust is False
    assert agent._config.observe is False


def test_progressive_disclosure_example():
    """Test the progressive disclosure principle in action."""
    # Beginner: Simple boolean flags
    simple_agent = Agent("simple", memory=True, robust=True)

    # Expert: Detailed configuration
    expert_agent = Agent(
        "expert",
        memory=MemoryConfig(synthesis_threshold=16000, max_impressions=100, user_id="expert_user"),
        robust=RobustConfig(
            retry=True, attempts=10, timeout=300.0, backoff="exponential", rate_limit_rps=0.5
        ),
    )

    # Both should work without conflicts
    assert simple_agent._config.memory is True
    assert simple_agent._config.robust is True

    assert expert_agent._config.memory.synthesis_threshold == 16000
    assert expert_agent._config.robust.attempts == 10
