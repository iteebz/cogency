"""Cogency - A framework for building intelligent agents.

This package provides a clean, zero-ceremony API for creating AI agents that can
reason, act, and respond using tools and memory. The core components are:

- Agent: Main class for agent creation and execution
- Config classes: For customizing memory, observability, and persistence

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
    from cogency import Agent, Tool, tool

    @tool
    class Calculator(Tool):
        def __init__(self):
            super().__init__("calc", "Calculator", "calc(expr: str)")
        async def run(self, expr: str):
            return {"result": eval(expr)}

    agent = Agent(
        "research_assistant",
        memory=True,
        tools=[Files(), Shell(), Calculator()]
    )
    ```
"""

# Public: Core agent class for creating intelligent assistants
from .agent import Agent

# Public: Configuration classes for customizing agent behavior
from .config import PersistConfig

# Public: Provider classes for explicit configuration
from .providers import Anthropic, Gemini, Mistral, Nomic, Ollama, OpenAI, Provider

# Public: Tool classes and system for explicit imports
from .tools import Files, Retrieval, Scrape, Search, Shell, Tool, tool

__all__ = [
    "Agent",
    "PersistConfig",
    "Files",
    "Retrieval",
    "Scrape",
    "Search",
    "Shell",
    "Tool",
    "tool",
    "OpenAI",
    "Anthropic",
    "Gemini",
    "Mistral",
    "Nomic",
    "Ollama",
    "Provider",
]
