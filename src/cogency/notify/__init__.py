"""Notification system for real-time agent feedback.

This module provides internal notification system for agent observability.
Notification components are implementation details and should not be accessed directly.

For custom feedback: Use Agent(observe=True) and observability exporters
For logging integration: Use standard Python logging with cogency loggers

Internal components:
- Notifier: Core notification dispatcher
- Formatters: CLI, Emoji, JSON formatting options
- emit: Function for sending notifications
- _setup_formatter: Utility for formatter configuration
"""

# Internal notification system - not exported
from .core import Notification, emit  # noqa: F401
from .formatters import CLIFormatter, EmojiFormatter, Formatter, JSONFormatter  # noqa: F401
from .notifier import Notifier  # noqa: F401
from .setup import _setup_formatter  # noqa: F401

# No public exports - use observability APIs instead
__all__ = []
