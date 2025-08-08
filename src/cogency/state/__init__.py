"""Agent state management - Database-as-State architecture.

Pure data + pure functions = beautiful state management.
"""

from .agent import State, UserProfile  # noqa: F401
from .modes import AgentMode  # noqa: F401

# Compatibility aliases for tests
ExecutionState = State

__all__ = []
