"""Tool registry - auto-discovery and initialization of all available tools."""

from .base import Tool
from .calculator import Calculator
from .code import Code
from .csv import CSV
from .date import Date
from .executor import run_tools
from .files import Files
from .http import HTTP
from .recall import Recall
from .registry import build_registry, get_tools, setup_tools, tool
from .scrape import Scrape
from .search import Search
from .shell import Shell
from .sql import SQL
from .time import Time
from .weather import Weather

__all__ = [
    "Tool",
    "Calculator",
    "Code",
    "CSV",
    "Date",
    "Files",
    "HTTP",
    "Recall",
    "Scrape",
    "Search",
    "Shell",
    "SQL",
    "Time",
    "Weather",
    "get_tools",
    "build_registry",
    "tool",
    "setup_tools",
    "run_tools",
]
