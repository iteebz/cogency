"""Shared utilities for robust operation.

This module provides utility functions for common operations:

- KeyManager: API key detection and rotation utilities

Additional internal utilities exist but are not exposed to maintain a clean
public API surface.
"""

# Public utilities for advanced usage
from .keys import KeyManager

__all__ = ["KeyManager"]
