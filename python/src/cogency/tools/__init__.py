# Centralized Tool Registry
# Tools are auto-discovered from this module

import importlib
import inspect
import os
from pathlib import Path

from cogency.tools.base import BaseTool


def _discover_tools():
    """Auto-discover all Tool classes in the tools directory."""
    tools_dir = Path(__file__).parent
    tool_classes = []

    # Scan all Python files in tools directory
    for file_path in tools_dir.glob("*.py"):
        if file_path.name.startswith("_"):
            continue

        module_name = f"cogency.tools.{file_path.stem}"
        try:
            module = importlib.import_module(module_name)
            for name, obj in inspect.getmembers(module):
                if (
                    inspect.isclass(obj)
                    and issubclass(obj, BaseTool)
                    and obj is not BaseTool
                ):
                    tool_classes.append(obj)
        except ImportError:
            continue

    return tool_classes


# Auto-discovered tools
AVAILABLE_TOOLS = _discover_tools()

# Tool registry by name for dynamic lookup
TOOL_REGISTRY = {tool().name: tool for tool in AVAILABLE_TOOLS}


def get_tool_by_name(name: str):
    """Get tool class by name."""
    return TOOL_REGISTRY.get(name)


def list_available_tools():
    """List all available tool names."""
    return list(TOOL_REGISTRY.keys())
