"""Cogency - A framework for building intelligent agents."""

# Clean public API - agent + config
from .agent import Agent
from .config import MemoryConfig, ObserveConfig, PersistConfig, RobustConfig

__all__ = [
    "Agent",
    "MemoryConfig",
    "ObserveConfig",
    "PersistConfig",
    "RobustConfig",
]
