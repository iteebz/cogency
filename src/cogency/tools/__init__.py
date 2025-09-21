"""Tooling system for Cogency.

Exposes a single, canonical, callable `tools` object that provides access
to all agent tools.
"""

from ..core.protocols import Tool
from .registry import ToolRegistry

# A single, canonical instance of the ToolRegistry that auto-discovers all built-in tools.
# This is the main export and the primary API for the tools system.
tools = ToolRegistry()

__all__ = ["tools", "ToolRegistry", "Tool"]
