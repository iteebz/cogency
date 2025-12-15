"""Cogency: Streaming agents."""

# Load environment variables FIRST - before any imports that need API keys
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

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
from .core.agent import Agent
from .tools import tools

__version__ = "3.3.0"
__all__ = [
    "Agent",
    "CogencyError",
    "ConfigError",
    "LLM",
    "LLMError",
    "ProtocolError",
    "Storage",
    "StorageError",
    "Tool",
    "ToolError",
    "ToolResult",
    "tools",
]
