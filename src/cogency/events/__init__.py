"""Event system for agent observability.

For event access: Use agent.logs() method
For custom handlers: Use Agent(handlers=[callback_function])

Example:
    def my_handler(event):
        print(f"Event: {event['type']}")

    agent = Agent("assistant", handlers=[my_handler])

Internal components:
- MessageBus, emit, init_bus: Core event infrastructure
- ConsoleHandler, LoggerHandler: Built-in handlers
"""

from .console import ConsoleHandler  # noqa: F401
from .core import MessageBus, component, emit, get_logs, init_bus  # noqa: F401
from .handlers import LoggerHandler  # noqa: F401

__all__ = []  # All internal - use bare functions for custom handlers
