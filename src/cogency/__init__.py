"""Cogency: Streaming agents."""

# Load environment variables FIRST - before any imports that need API keys
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

from .core import LLM, Storage, Tool, ToolResult
from .core.agent import Agent
from .core.exceptions import AgentError, CogencyError, ProfileError, ProviderError, ToolError
from .tools import tools

__version__ = "3.0.0"
__all__ = [
    "Agent",
    "AgentError",
    "CogencyError",
    "LLM",
    "ProfileError",
    "ProviderError",
    "Storage",
    "Tool",
    "ToolError",
    "ToolResult",
    "tools",
]
