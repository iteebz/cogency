"""Cogency tools with individual exports and convenience factory."""

# File tools
from .file import FileEdit, FileList, FileRead, FileSearch, FileWrite

# Memory tools
from .memory import MemoryRecall

# Convenience factory (registry)
from .registry import ToolRegistry

# System tools
from .system import SystemShell

# Web tools
from .web import WebScrape, WebSearch

# Create convenience instance
tools = ToolRegistry()

__all__ = [
    # Individual tools for configuration
    "FileRead",
    "FileWrite",
    "FileEdit",
    "FileList",
    "FileSearch",
    "SystemShell",
    "WebScrape",
    "WebSearch",
    "MemoryRecall",
    # Convenience factory
    "tools",
]
