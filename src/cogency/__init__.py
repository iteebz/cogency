"""Cogency: Streaming agents."""

# Load environment variables FIRST - before any imports that need API keys
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

from .agent import Agent
from .core import (
    LLM,
    CogencyError,
    ConfigError,
    LLMError,
    ProtocolError,
    Storage,
    StorageError,
    Tool,
    ToolError,
    ToolResult,
)
from .tools import tools

__version__ = "3.3.0"
__all__ = [
    "LLM",
    "Agent",
    "CogencyError",
    "ConfigError",
    "LLMError",
    "ProtocolError",
    "Storage",
    "StorageError",
    "Tool",
    "ToolError",
    "ToolResult",
    "tools",
]
