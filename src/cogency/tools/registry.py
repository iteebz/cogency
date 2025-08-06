"""Tool registry."""

import logging
from typing import List, Type, Union

from cogency.tools.base import Tool

logger = logging.getLogger(__name__)


def _setup_tools(tools, memory):
    """Setup tools with explicit configuration."""
    if tools is None:
        raise ValueError(
            "tools must be explicitly specified; use [] for no tools or 'all' for full access"
        )

    if tools == "all":
        return ToolRegistry.get_tools()
    elif isinstance(tools, str):
        raise ValueError(f"Invalid tools value '{tools}'; use 'all' or a list of tools")
    elif isinstance(tools, list):
        resolved = _resolve_tool_list(tools)

        # Developer hint when no tools configured but tools are registered
        if not resolved and ToolRegistry._tools:
            from cogency.events import emit

            registered_count = len(ToolRegistry._tools)
            emit(
                "agent",
                operation="setup",
                status="no_tools_configured",
                message=f"Agent initialized with no tools, but {registered_count} tools are registered. Use tools='all' to enable them.",
                registered_tools=[cls.__name__ for cls in ToolRegistry._tools],
            )

        return resolved

    return tools


def _resolve_tool_list(tools: List[Union[str, Tool]]) -> List[Tool]:
    """Resolve list of tool instances."""
    resolved = []

    for tool in tools:
        if isinstance(tool, str):
            tool_instance = _get_tool(tool)
            if tool_instance:
                resolved.append(tool_instance)
            else:
                logger.warning(f"Unknown tool name: {tool}")
        elif isinstance(tool, Tool):
            resolved.append(tool)
        else:
            logger.warning(f"Invalid tool type: {type(tool)}")

    return resolved


def _get_tool(name: str) -> Tool:
    """Get tool instance by name."""
    from cogency.events import emit

    # Import here to avoid circular imports
    from cogency.tools.files import Files
    from cogency.tools.scrape import Scrape
    from cogency.tools.search import Search
    from cogency.tools.shell import Shell

    tool_map = {
        "files": Files,
        "scrape": Scrape,
        "search": Search,
        "shell": Shell,
    }

    emit("tool", operation="load", name=name, status="start")

    tool_class = tool_map.get(name.lower())
    if tool_class:
        try:
            tool_instance = tool_class()
            emit(
                "tool",
                operation="load",
                name=name,
                status="complete",
                class_name=tool_class.__name__,
            )
            return tool_instance
        except Exception as e:
            emit("tool", operation="load", name=name, status="error", error=str(e))
            logger.debug(f"Failed to instantiate {name}: {e}")
            return None

    emit("tool", operation="load", name=name, status="not_found")
    return None


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
        """Get all registered tool instances - zero ceremony instantiation."""
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
    """Get all registered tool instances.

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
