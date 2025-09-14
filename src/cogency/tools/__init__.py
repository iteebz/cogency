"""Tools: Minimal tool interface for ReAct agents."""

from ..core.protocols import Tool
from .file import FileEdit, FileList, FileRead, FileSearch, FileWrite
from .memory import MemoryRecall
from .system import SystemShell
from .web import WebScrape, WebSearch

TOOLS = [
    FileRead(),
    FileWrite(),
    FileEdit(),
    FileList(),
    FileSearch(),
    SystemShell(),
    WebSearch(),
    WebScrape(),
    MemoryRecall(),
]


def instructions(tools: list) -> str:
    """Generate clean toolbox listing for agent awareness."""
    lines = []
    for tool in tools:
        params = []
        if hasattr(tool, "schema") and tool.schema:
            for param, info in tool.schema.items():
                if info.get("required", True):
                    params.append(param)
                else:
                    params.append(f"{param}?")
        param_str = ", ".join(params)
        lines.append(f"{tool.name}({param_str}) - {tool.description}")
    return "TOOLBOX:\n" + "\n".join(lines)


__all__ = [
    "Tool",
    "TOOLS",
    "instructions",
    "FileRead",
    "FileWrite",
    "FileEdit",
    "FileList",
    "FileSearch",
    "MemoryRecall",
    "SystemShell",
    "WebSearch",
    "WebScrape",
]
