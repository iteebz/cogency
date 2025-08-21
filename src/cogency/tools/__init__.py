"""Tools: Minimal tool interface for ReAct agents."""

from ..core.protocols import Tool
from .file import FileList, FileRead, FileWrite
from .scrape import Scrape
from .search import Search
from .shell import Shell

BASIC_TOOLS = [
    FileRead(),
    FileWrite(),
    FileList(),
    Shell(),
    Search(),
    Scrape(),
]

__all__ = [
    "Tool",
    "BASIC_TOOLS",
    "FileRead",
    "FileWrite",
    "FileList",
    "Shell",
    "Search",
    "Scrape",
]
