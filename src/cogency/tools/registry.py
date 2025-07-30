"""Tool registry for auto-discovery."""

import logging
from typing import List, Type

from cogency.tools.base import Tool

logger = logging.getLogger(__name__)


def setup_tools(tools, memory):
    """Setup tools with auto-discovery and recall integration."""
    if tools is None:
        # Auto-discover tools
        tools = ToolRegistry.get_tools(memory=memory)

    # Add recall tool if memory enabled
    if memory:
        from cogency.tools import Recall

        if not any(isinstance(tool, Recall) for tool in tools):
            tools.append(Recall(memory))

    return tools


class ToolRegistry:
    """Auto-discovery registry for tools."""

    _tools: List[Type[Tool]] = []

    @classmethod
    def add(cls, tool_class: Type[Tool]):
        """Register a tool class for auto-discovery."""
        if tool_class not in cls._tools:
            cls._tools.append(tool_class)
        return tool_class

    @classmethod
    def get_tools(cls, **kwargs) -> List[Tool]:
        """Get all registered tool instances - zero ceremony instantiation."""
        tools = []
        for tool_class in cls._tools:
            try:
                # Try with kwargs first, fallback to no-args
                try:
                    tools.append(tool_class(**kwargs))
                except TypeError:
                    tools.append(tool_class())
            except Exception as e:
                logger.debug(f"Skipped {tool_class.__name__}: {e}")
                continue
        return tools

    @classmethod
    def clear(cls):
        """Clear registry (mainly for testing)."""
        cls._tools.clear()


def tool(cls):
    """Decorator to auto-register tools."""
    return ToolRegistry.add(cls)


def get_tools(**kwargs) -> List[Tool]:
    """Get all registered tool instances."""
    return ToolRegistry.get_tools(**kwargs)


def build_registry(tools: List[Tool], lite: bool = False) -> str:
    """Build tool registry with optional details."""
    if not tools:
        return "no tools"

    entries = []

    for tool_instance in tools:
        if lite:
            entries.append(
                f"{tool_instance.emoji} [{tool_instance.name}]: {tool_instance.description}"
            )
        else:
            rules_str = (
                "\n".join(f"- {r}" for r in tool_instance.rules) if tool_instance.rules else "None"
            )
            examples_str = (
                "\n".join(f"- {e}" for e in tool_instance.examples)
                if tool_instance.examples
                else "None"
            )

            entry = f"{tool_instance.emoji} [{tool_instance.name}]\n{tool_instance.description}\n\n"
            entry += f"{tool_instance.schema}\n\n"
            entry += f"Rules:\n{rules_str}\n\n"
            entry += f"Examples:\n{examples_str}\n"
            entry += "---"
            entries.append(entry)
    return "\n".join(entries)
