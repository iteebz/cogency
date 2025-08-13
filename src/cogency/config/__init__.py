"""Configuration classes for agent customization.

This module provides configuration dataclasses for customizing agent behavior:

- PathsConfig: Configure file paths (advanced usage)
- MAX_TOOL_CALLS: Maximum tool calls per reasoning cycle
"""

from .dataclasses import (
    MAX_TOOL_CALLS,
    PathsConfig,
)

__all__ = [
    "MAX_TOOL_CALLS",
    "PathsConfig",
]
