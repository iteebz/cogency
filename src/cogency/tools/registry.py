"""Tool registry for auto-discovery."""

import contextlib
import importlib
import inspect
import logging
from pathlib import Path
from typing import Any, Dict, List, Type

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


def get_tools(**kwargs) -> List[Tool]:
    """Get all registered tool instances."""
    return ToolRegistry.get_tools(**kwargs)


def get_tool_classes() -> Dict[str, Any]:
    """Auto-discover tool classes for direct import."""
    # Auto-discover tools by importing all tool modules and collect exported classes
    _tools_dir = Path(__file__).parent
    _exported_classes: Dict[str, Any] = {}

    for tool_file in _tools_dir.glob("*.py"):
        if tool_file.name not in ["__init__.py", "base.py", "registry.py", "executor.py"]:
            module_name = f"cogency.tools.{tool_file.stem}"
            with contextlib.suppress(ImportError):
                module = importlib.import_module(module_name)
                # Export tool classes that are decorated with @tool
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if isinstance(attr, type) and issubclass(attr, Tool) and attr is not Tool:
                        _exported_classes[attr_name] = attr

    return _exported_classes


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
