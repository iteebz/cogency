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
from cogency.tools.recall import RecallTool

# Export all tools for easy importing
__all__ = [
    "BaseTool",
    "CalculatorTool",
    "FileManagerTool", 
    "TimezoneTool",
    "WeatherTool",
    "WebSearchTool",
    "RecallTool",
]