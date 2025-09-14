"""Cogency: Streaming agents."""

# Load environment variables FIRST - before any imports that need API keys
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

from .core import Tool
from .core.agent import Agent
from .core.protocols import ToolResult
from .tools import TOOLS

__version__ = "3.0.0"
__all__ = ["Agent", "Tool", "ToolResult", "TOOLS"]
