"""Agent state management with separated concerns.

This module provides internal state architecture for agent execution.
State objects are implementation details and should not be accessed directly.

For debugging: Use Agent(observe=True) and observability hooks
For persistence: Use PersistConfig and Store interfaces

Internal components:
- AgentState: Main state container for agent execution
- ExecutionState: Manages execution flow and tool calls
- AgentMode: Execution mode enumeration
- ReasoningContext: Context for reasoning operations
- UserProfile: User preference and context management
"""

# Internal state management - not exported
from .agent import AgentState  # noqa: F401
from .execution import AgentMode, ExecutionState  # noqa: F401
from .reasoning import ReasoningContext  # noqa: F401
from .user import UserProfile  # noqa: F401

# No public exports - use Agent APIs instead
__all__ = []
