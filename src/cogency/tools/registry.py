"""Tool registry."""

import logging
from typing import List, Type

from cogency.tools.base import Tool

logger = logging.getLogger(__name__)


def _setup_tools(tools, memory):
    """Setup tools with explicit configuration."""
    if tools is None:
        raise ValueError(
            "tools must be explicitly specified; use [] for no tools or [Tool(), ...] for specific tools"
        )

    if isinstance(tools, str):
        raise ValueError(
            f"Invalid tools value '{tools}'; use [] or [Tool(), ...] with explicit instances"
        )
    elif isinstance(tools, list):
        # Validate all items are Tool instances
        for tool in tools:
            if not isinstance(tool, Tool):
                raise ValueError(
                    f"Invalid tool type: {type(tool)}. Use Tool() instances, not strings or classes"
                )
        return tools

    return tools


class ToolRegistry:
    """Registry for tools."""

    _tools: List[Type[Tool]] = []

    @classmethod
    def add(cls, tool_class: Type[Tool]):
        """Register a tool class."""
        if tool_class not in cls._tools:
            cls._tools.append(tool_class)
        return tool_class

    @classmethod
    def get_tools(cls, **kwargs) -> List[Tool]:
        """Get all registered tool instances - internal use only."""
        from cogency.events import emit

        emit("tool", operation="registry", status="start", count=len(cls._tools))

        tools = []
        for tool_class in cls._tools:
            try:
                # Consistent no-args instantiation
                tool_instance = tool_class()
                tools.append(tool_instance)
                emit("tool", operation="registry", status="loaded", name=tool_class.__name__)
            except Exception as e:
                emit(
                    "tool",
                    operation="registry",
                    status="skipped",
                    name=tool_class.__name__,
                    error=str(e),
                )
                logger.debug(f"Skipped {tool_class.__name__}: {e}")
                continue

        emit(
            "tool",
            operation="registry",
            status="complete",
            loaded=len(tools),
            total=len(cls._tools),
        )
        return tools

    @classmethod
    def clear(cls):
        """Clear registry (mainly for testing)."""
        cls._tools.clear()


def tool(cls):
    """Decorator to auto-register tools."""
    return ToolRegistry.add(cls)


def get_tools(**kwargs) -> List[Tool]:
    """Get all registered tool instances - internal use only.

    Args:
        **kwargs: Optional arguments passed to tool constructors

    Returns:
        List of instantiated Tool objects
    """
    return ToolRegistry.get_tools(**kwargs)


def build_tool_descriptions(tools: List[Tool]) -> str:
    """Build brief tool descriptions for triage/overview contexts."""
    if not tools:
        return "no tools"

    entries = []
    for tool_instance in tools:
        entries.append(f"{tool_instance.emoji} [{tool_instance.name}]: {tool_instance.description}")
    return "\n".join(entries)


def build_tool_schemas(tools: List[Tool]) -> str:
    """Build tool schemas with examples and rules - no JSON conversion."""
    if not tools:
        return "no tools"

    entries = []
    for tool_instance in tools:
        rules_str = (
            "\n".join(f"- {r}" for r in tool_instance.rules) if tool_instance.rules else "None"
        )
        examples_str = (
            "\n".join(f"- {e}" for e in tool_instance.examples)
            if tool_instance.examples
            else "None"
        )

        entry = f"{tool_instance.emoji} [{tool_instance.name}]\n{tool_instance.description}\n\n"
        entry += f"Rules:\n{rules_str}\n\n"
        entry += f"Examples:\n{examples_str}\n"
        entry += "---"
        entries.append(entry)
    return "\n".join(entries)
