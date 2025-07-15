# Centralized Tool Registry
# Tools are auto-discovered from this module

import importlib
import inspect
from pathlib import Path

from cogency.tools.base import BaseTool

# Explicit imports for clean API
from cogency.tools.calculator import CalculatorTool
from cogency.tools.file_manager import FileManagerTool
from cogency.tools.timezone import TimezoneTool
from cogency.tools.weather import WeatherTool
from cogency.tools.web_search import WebSearchTool
from cogency.tools.memory import MemorizeTool, RecallTool

# Export all tools for easy importing
__all__ = [
    "BaseTool",
    "CalculatorTool",
    "FileManagerTool", 
    "TimezoneTool",
    "WeatherTool",
    "WebSearchTool",
    "MemorizeTool",
    "RecallTool",
    "AVAILABLE_TOOLS",
    "TOOL_REGISTRY",
    "get_tool_by_name",
    "list_available_tools",
]


def _discover_tools():
    """Auto-discover only standalone tool classes."""
    return [
        CalculatorTool,
        FileManagerTool,
        TimezoneTool, 
        WeatherTool,
        WebSearchTool
    ]


# Auto-discovered tools
AVAILABLE_TOOLS = _discover_tools()

# Tool registry by name for dynamic lookup (standalone tools only)
TOOL_REGISTRY = {tool().name: tool for tool in AVAILABLE_TOOLS}


def get_tool_by_name(name: str):
    """Get tool class by name."""
    return TOOL_REGISTRY.get(name)


def list_available_tools():
    """List all available tool names."""
    return list(TOOL_REGISTRY.keys())
