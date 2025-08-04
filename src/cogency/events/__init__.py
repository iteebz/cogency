"""Event system for agent observability.

For event access: Use agent.logs() method
For custom streaming: Use Agent(handlers=[callback_function])

Internal components:
- MessageBus, emit, init_bus: Core event infrastructure
- ConsoleHandler, LoggerHandler: Built-in handlers
"""

from .console import ConsoleHandler, console_callback  # noqa: F401
from .core import MessageBus, component, emit, get_logs, init_bus  # noqa: F401
from .handlers import LoggerHandler  # noqa: F401

__all__ = []  # All internal
