"""Event system for agent observability.

Tactical message bus for comprehensive agent monitoring and debugging.
Event system components are internal implementation details.

For event access: Use agent.logs() method
For custom streaming: Use Agent(handlers=[CallbackHandler(callback)])

Internal components:
- MessageBus, emit, init_bus: Core event infrastructure
- ConsoleHandler, LoggerHandler: Built-in handlers
"""

# Internal event system - not exported
from .core import MessageBus, component, emit, init_bus  # noqa: F401

# Public: Custom event streaming handler
from .handlers import CallbackHandler, ConsoleHandler, LoggerHandler  # noqa: F401

__all__ = [
    "CallbackHandler",
]
