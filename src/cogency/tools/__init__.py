"""Tools: Minimal tool interface for ReAct agents."""

from ..core.protocols import Tool
from .files import FileList, FileRead, FileWrite
from .retrieve import Retrieve
from .scrape import Scrape
from .search import Search
from .shell import Shell

BASIC_TOOLS = [FileRead(), FileWrite(), FileList(), Shell(), Retrieve(), Search(), Scrape()]

__all__ = [
    "Tool",
    "BASIC_TOOLS",
    "FileRead",
    "FileWrite",
    "FileList",
    "Shell",
    "Retrieve",
    "Search",
    "Scrape",
]
