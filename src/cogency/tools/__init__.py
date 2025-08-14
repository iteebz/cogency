"""Tools: Minimal tool interface for ReAct agents."""

from .base import Tool
from .files import FileList, FileRead, FileWrite
from .retrieve import Retrieve
from .shell import Shell

BASIC_TOOLS = [FileRead(), FileWrite(), FileList(), Shell(), Retrieve()]

__all__ = ["Tool", "BASIC_TOOLS", "FileRead", "FileWrite", "FileList", "Shell", "Retrieve"]
