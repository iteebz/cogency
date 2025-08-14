"""Cogency: Stateless Context-Driven Agent Framework

Context injection + LLM inference = complete reasoning engine.
"""

from .agent import Agent
from .context import set_user_profile
from .react import ReActAgent
from .tools import BASIC_TOOLS, Tool

__version__ = "2.0.0"
__all__ = ["Agent", "ReActAgent", "Tool", "BASIC_TOOLS", "set_user_profile"]
