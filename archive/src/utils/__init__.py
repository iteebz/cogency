"""Shared utilities for robust operation.

This module provides utility functions for common operations:

- Credentials: Universal credential detection for any service

Additional internal utilities exist but are not exposed to maintain a clean
public API surface.
"""

# Public utilities for advanced usage
from .credentials import Credentials

__all__ = ["Credentials"]
