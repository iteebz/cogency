"""Tool system for agent capabilities.

This module provides the tool system that enables agents to interact with external
systems and perform actions. It includes:

- Tool: Base class for creating custom tools
- Built-in tools: Files, Scrape, Search, Shell
- @tool: Decorator for registering tool functions
- get_tools: Utility for accessing registered tools

Example:
    Using built-in tools:

    ```python
    from cogency import Agent
    from cogency.tools import Files

    agent = Agent("assistant", tools=[Files()])
    ```

    Creating custom tools:

    ```python
    from cogency.tools import tool

    @tool
    def calculator(expression: str) -> float:
        '''Simple calculator tool.'''
        return eval(expression)
    ```
"""

# Public: Base class for creating custom tools
from .base import Tool

# Public: Built-in file operations tool
from .files import Files

# Public: Core tool system functions for registration and LLM integration
from .registry import (
    build_tool_descriptions,  # Public: Brief tool descriptions for triage/overview
    build_tool_schemas,  # Public: Complete schemas with examples for LLM execution
    get_tools,  # Public: Access all registered tools for custom agent initialization
    tool,  # Public: Decorator for registering custom tool classes
)

# Public: Built-in web scraping tool
from .scrape import Scrape

# Public: Built-in web search tool
from .search import Search

# Public: Built-in shell command tool
from .shell import Shell

__all__ = [
    # Public tool APIs
    "Tool",  # Base class for custom tools
    "Files",  # Built-in file operations
    "Scrape",  # Built-in web scraping
    "Search",  # Built-in web search
    "Shell",  # Built-in shell commands
    "tool",  # Decorator for tool registration
    "get_tools",  # Get registered tools (advanced usage)
    "build_tool_descriptions",  # Brief tool descriptions for triage/overview
    "build_tool_schemas",  # Complete schemas with examples for LLM execution
]
