"""CLI interface - deprecated, use cogency.cli.main instead."""

# Backward compatibility imports
from cogency.cli.interactive import interactive_mode
from cogency.cli.main import main

__all__ = ["main", "interactive_mode"]

# All other functions have been moved to cogency.cli namespace
