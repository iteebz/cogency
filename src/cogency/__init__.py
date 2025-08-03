"""Cogency - A framework for building intelligent agents.

This package provides a clean, zero-ceremony API for creating AI agents that can
reason, act, and respond using tools and memory. The core components are:

- Agent: Main class for agent creation and execution
- Config classes: For customizing memory, observability, persistence, and robustness

Example:
    Basic agent usage:

    ```python
    from cogency import Agent

    agent = Agent("assistant")
    result = agent.run("Hello, how can you help?")
    print(result)
    ```

    With configuration:

    ```python
    from cogency import Agent, MemoryConfig, ObserveConfig

    agent = Agent(
        "research_assistant",
        memory=MemoryConfig(),
        observe=ObserveConfig()
    )
    ```
"""

# Public: Core agent class for creating intelligent assistants
from .agent import Agent

# Public: Configuration classes for customizing agent behavior
from .config import MemoryConfig, ObserveConfig, PersistConfig, RobustConfig

__all__ = [
    "Agent",
    "MemoryConfig",
    "ObserveConfig",
    "PersistConfig",
    "RobustConfig",
]
