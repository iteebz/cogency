"""Cogency: Context-driven agent framework."""

from .core import Agent, AgentResult
from .core.protocols import Tool
from .lib import Err, Ok, Result
from .tools import BASIC_TOOLS

__version__ = "2.1.0"
__all__ = ["Agent", "AgentResult", "Result", "Ok", "Err", "Tool", "BASIC_TOOLS"]
