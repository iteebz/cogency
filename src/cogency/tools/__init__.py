"""Tool registry - auto-discovery and initialization of all available tools."""

from .base import Tool
from .files import Files
from .http import HTTP
from .registry import build_registry, get_tools, setup_tools, tool
from .scrape import Scrape
from .search import Search
from .shell import Shell

__all__ = [
    "Tool",
    "Files",
    "HTTP",
    "Scrape",
    "Search",
    "Shell",
    "get_tools",
    "build_registry",
    "tool",
    "setup_tools",
]
