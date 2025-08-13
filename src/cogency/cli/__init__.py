"""CLI interface - zero ceremony entry point."""

from .interactive import interactive_mode
from .main import main

__all__ = ["main", "interactive_mode"]
