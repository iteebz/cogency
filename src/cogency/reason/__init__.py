"""Reasoning namespace - context to decisions transformation.

Core reasoning primitive: analyze context and produce decisions.
Supports the 'reason' step in agent execution loops.
"""

from .analyze import reason

__all__ = ["reason"]
