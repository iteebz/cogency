"""Tools: Minimal tool interface for ReAct agents."""

from ..core.protocols import Tool
from .file import FileEdit, FileList, FileRead, FileWrite
from .memory import MemoryRecall
from .system import SystemShell
from .web import WebScrape, WebSearch

TOOLS = [
    FileRead(),
    FileWrite(),
    FileEdit(),
    FileList(),
    SystemShell(),
    WebSearch(),
    WebScrape(),
    MemoryRecall(),
]

__all__ = [
    "Tool",
    "TOOLS",
    "FileRead",
    "FileWrite",
    "FileEdit",
    "FileList",
    "MemoryRecall",
    "SystemShell",
    "WebSearch",
    "WebScrape",
]
