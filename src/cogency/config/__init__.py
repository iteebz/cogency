"""Configuration classes for agent customization.

This module provides configuration dataclasses for customizing agent behavior:

- MemoryConfig: Configure memory and impression synthesis
- ObserveConfig: Configure metrics and observability
- PersistConfig: Configure state persistence
- RobustConfig: Configure retry and resilience behavior
- PathsConfig: Configure file paths (advanced usage)
- MAX_TOOL_CALLS: Maximum tool calls per reasoning cycle

Example:
    ```python
    from cogency import Agent, MemoryConfig, ObserveConfig

    agent = Agent(
        "assistant",
        memory=MemoryConfig(max_tokens=1000),
        observe=ObserveConfig(prometheus=True)
    )
    ```
"""

from .dataclasses import (
    MAX_TOOL_CALLS,
    MemoryConfig,
    ObserveConfig,
    PathsConfig,
    PersistConfig,
    RobustConfig,
)

__all__ = [
    "MAX_TOOL_CALLS",
    "MemoryConfig",
    "ObserveConfig",
    "PathsConfig",
    "PersistConfig",
    "RobustConfig",
]
