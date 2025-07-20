# Centralized Tool Registry
# Tools are auto-discovered from this module

import importlib
import inspect
from pathlib import Path

from cogency.tools.base import BaseTool

# Explicit imports for clean API
from cogency.tools.calculator import Calculator
from cogency.tools.file import File
from cogency.tools.time import Time
from cogency.tools.date import Date
from cogency.tools.weather import Weather
from cogency.tools.search import Search
from cogency.tools.recall import Recall
from cogency.tools.http import HTTP
from cogency.tools.shell import Shell
from cogency.tools.code import Code

# Export all tools for easy importing
__all__ = [
    "BaseTool",
    "Calculator",
    "File", 
    "Date",
    "Time",
    "Weather",
    "Search",
    "Recall",
    "HTTP",
    "Shell",
    "Code",
]