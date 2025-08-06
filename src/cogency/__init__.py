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

    Streaming execution:

    ```python
    async for chunk in agent.stream("Research quantum computing"):
        print(chunk, end="", flush=True)
    ```

    With configuration and tools:

    ```python
    from cogency import Agent, MemoryConfig, Tool, tool

    @tool
    class Calculator(Tool):
        def __init__(self):
            super().__init__("calc", "Calculator", "calc(expr: str)")
        async def run(self, expr: str):
            return {"result": eval(expr)}

    agent = Agent(
        "research_assistant",
        memory=MemoryConfig(),
        tools="all"
    )
    ```
"""

# Public: Core agent class for creating intelligent assistants
from .agent import Agent

# Public: Configuration classes for customizing agent behavior
from .config import MemoryConfig, PersistConfig, RobustConfig

# Public: Tool classes and system for explicit imports
from .tools import Files, Scrape, Search, Shell, Tool, tool

__all__ = [
    "Agent",
    "MemoryConfig",
    "PersistConfig",
    "RobustConfig",
    "Files",
    "Scrape",
    "Search",
    "Shell",
    "Tool",
    "tool",
]
