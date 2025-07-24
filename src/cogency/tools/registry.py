"""Tool registry for auto-discovery."""

import inspect
import logging
from typing import List, Type

from .base import BaseTool

logger = logging.getLogger(__name__)


class ToolRegistry:
    """Auto-discovery registry for tools."""

    _tools: List[Type[BaseTool]] = []

    @classmethod
    def add(cls, tool_class: Type[BaseTool]):
        """Register a tool class for auto-discovery."""
        if tool_class not in cls._tools:
            cls._tools.append(tool_class)
        return tool_class

    @classmethod
    def get_tools(cls, **kwargs) -> List[BaseTool]:
        """Get all registered tool instances."""
        tools = []
        for tool_class in cls._tools:
            try:
                # Check if 'memory' is a required parameter for the tool's __init__
                sig = inspect.signature(tool_class.__init__)
                if (
                    "memory" in sig.parameters
                    and sig.parameters["memory"].kind == inspect.Parameter.POSITIONAL_OR_KEYWORD
                    and sig.parameters["memory"].default is inspect.Parameter.empty
                ):
                    # If 'memory' is a required parameter, try to instantiate with kwargs
                    if "memory" in kwargs:
                        tools.append(tool_class(**kwargs))
                    else:
                        # Skip if memory is required but not provided in kwargs
                        continue
                else:
                    # Otherwise, try to instantiate without kwargs first
                    try:
                        tools.append(tool_class())
                    except TypeError:
                        # Fallback to instantiating with kwargs if it fails without
                        tools.append(tool_class(**kwargs))
            except Exception as e:
                logger.error(f"Failed to instantiate tool {tool_class.__name__}: {e}")
                # Skip tools that can't be instantiated for any other reason
                continue
        return tools

    @classmethod
    def clear(cls):
        """Clear registry (mainly for testing)."""
        cls._tools.clear()


def tool(cls):
    """Decorator to auto-register tools."""
    return ToolRegistry.add(cls)


def get_tools(**kwargs) -> List[BaseTool]:
    """Get all registered tool instances."""
    return ToolRegistry.get_tools(**kwargs)


def build_registry(tools: List[BaseTool], lite: bool = False) -> str:
    """Build tool registry with optional details."""
    if not tools:
        return "no tools"

    entries = []
    for tool in tools:
        if lite:
            entries.append(f"{tool.emoji} [{tool.name}]: {tool.description}")
        else:
            rules_str = "\n".join(f"- {r}" for r in tool.rules) if tool.rules else "None"
            examples_str = "\n".join(f"- {e}" for e in tool.examples) if tool.examples else "None"

            entry = f"{tool.emoji} [{tool.name}]\n{tool.description}\n\n"
            entry += f"{tool.schema}\n\n"
            entry += f"Rules:\n{rules_str}\n\n"
            entry += f"Examples:\n{examples_str}\n"
            entry += "---"
            entries.append(entry)
    return "\n".join(entries)
