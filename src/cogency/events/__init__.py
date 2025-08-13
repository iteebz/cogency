"""Event system for agent observability.

For event access: Use agent.logs() method
For custom handlers: Use Agent(handlers=[callback_function])

Example:
    def my_handler(event):
        print(f"Event: {event['type']}")

    agent = Agent("assistant", handlers=[my_handler])

Internal components:
- MessageBus, emit, init_bus: Core event infrastructure
- ConsoleHandler, EventBuffer: Built-in handlers
"""

from .bus import MessageBus, emit, get_logs, init_bus  # noqa: F401
from .console import ConsoleHandler  # noqa: F401
from .handlers import EventBuffer, EventLogger  # noqa: F401
from .lifecycle import lifecycle  # noqa: F401
from .logs import (  # noqa: F401
    LogsBridge,
    create_logs_bridge,
    format_logs_summary,
)
from .orchestration import state_event  # noqa: F401
from .streaming import StreamingCoordinator, format_stream_event  # noqa: F401

__all__ = []  # All internal - use bare functions for custom handlers
