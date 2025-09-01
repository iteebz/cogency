"""Cogency: Streaming consciousness for AI agents."""

# Load environment variables FIRST - before any imports that need API keys
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

from .core import Tool
from .core.agent import Agent
from .lib import Err, Ok, Result
from .tools import TOOLS

__version__ = "3.0.0"
__all__ = ["Agent", "Result", "Ok", "Err", "Tool", "TOOLS"]
