"""Tool system for agent capabilities.

This module provides the tool system that enables agents to interact with external
systems and perform actions. It includes:

- Tool: Base class for creating custom tools
- Built-in tools: Files, Retrieve, Scrape, Search, Shell
- @tool: Decorator for registering tool functions

Example:
    Using built-in tools:

    ```python
    from cogency import Agent
    from cogency.tools import Files, Retrieve

    agent = Agent("assistant", tools=[Files(), Retrieve()])
    ```

    Creating custom tools:

    ```python
    from cogency.tools import tool

    @tool
    def calculator(a: float, b: float, operation: str) -> float:
        '''Simple calculator tool.'''
        if operation == 'add':
            return a + b
        elif operation == 'multiply':
            return a * b
        # etc...
    ```
"""

# Public: Base class for creating custom tools
from .base import Tool

# Public: Built-in file operations tool
from .files import Files

# Tool composition helpers removed - just use [Files(), Shell()] directly
# Built-in memory recall tool moved to memory domain - use @tool decorator instead
# Public: Core tool system functions for registration and LLM integration
from .registry import (
    build_tool_descriptions,  # Public: Brief tool descriptions for triage/overview
    build_tool_schemas,  # Public: Complete schemas with examples for LLM execution
    tool,  # Public: Decorator for registering custom tool classes
)

# Public: Built-in web scraping tool
from .scrape import Scrape

# Public: Built-in web search tool
from .search import Search

# Public: Tool security
from .security import SecurityResult, secure_response, secure_tool

# Public: Built-in shell command tool
from .shell import Shell

# Public: Tool argument validation
from .validation import validate

# Note: Retrieve moved to cogency.context.knowledge - import directly from there


__all__ = [
    # Public tool APIs
    "Tool",  # Base class for custom tools
    "Files",  # Built-in file operations
    "Scrape",  # Built-in web scraping
    "Search",  # Built-in web search
    "Shell",  # Built-in shell commands
    "tool",  # Decorator for tool registration
    "build_tool_descriptions",  # Brief tool descriptions for triage/overview
    "build_tool_schemas",  # Complete schemas with examples for LLM execution
    "validate",  # Tool argument validation
    "secure_tool",  # Tool security enforcement
    "secure_response",  # Response security
    "SecurityResult",  # Security result
]
