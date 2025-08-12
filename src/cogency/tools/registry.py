"""Tool registry."""

import logging

from cogency.tools.base import Tool

logger = logging.getLogger(__name__)


def _setup_tools(tools, embedder=None):
    """Setup tools with explicit configuration."""
    if tools is None:
        raise ValueError(
            "tools must be explicitly specified; use [] for no tools or [Tool(), ...] for specific tools"
        )

    if isinstance(tools, str):
        raise ValueError(
            f"Invalid tools value '{tools}'; use [] or [Tool(), ...] with explicit instances"
        )
    if isinstance(tools, list):
        # Validate all items are Tool instances and inject dependencies
        configured_tools = []
        for tool in tools:
            if not isinstance(tool, Tool):
                raise ValueError(
                    f"Invalid tool type: {type(tool)}. Use Tool() instances, not strings or classes"
                )

            # CANONICAL: Inject embedder into ALL semantic tools uniformly
            if embedder is not None and hasattr(tool, "_embedder"):
                tool._embedder = embedder

            configured_tools.append(tool)
        return configured_tools

    return tools


class ToolRegistry:
    """Registry for tools."""

    _tools: list[type[Tool]] = []

    @classmethod
    def add(cls, tool_class: type[Tool]):
        """Register a tool class."""
        if tool_class not in cls._tools:
            cls._tools.append(tool_class)
        return tool_class

    @classmethod
    def clear(cls):
        """Clear registry (mainly for testing)."""
        cls._tools.clear()


def tool(cls):
    """Decorator to auto-register tools."""
    return ToolRegistry.add(cls)


def build_tool_descriptions(tools: list[Tool]) -> str:
    """Build brief tool descriptions for triage/overview contexts."""
    if not tools:
        return "no tools"

    entries = []
    for tool_instance in tools:
        entries.append(f"{tool_instance.emoji} [{tool_instance.name}]: {tool_instance.description}")
    return "\n".join(entries)


def build_tool_schemas(tools: list[Tool]) -> str:
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
