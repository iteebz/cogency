"""Simple logging interface."""

import logging
import sys


class Logger:
    """Simple logger with debug control."""

    def __init__(self, name: str = "cogency"):
        self.logger = logging.getLogger(name)
        if not self.logger.handlers:
            self._setup()

    def _setup(self):
        """One-time setup with sensible defaults."""
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter("%(message)s"))
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)

    def debug(self, message: str):
        """Debug level logging."""
        self.logger.debug(message)

    def info(self, message: str):
        """Info level logging."""
        self.logger.info(message)

    def warning(self, message: str):
        """Warning level logging."""
        self.logger.warning(message)

    def error(self, message: str):
        """Error level logging."""
        self.logger.error(message)

    def set_debug(self, enabled: bool = True):
        """Enable/disable debug logging."""
        level = logging.DEBUG if enabled else logging.INFO
        self.logger.setLevel(level)


# Global instance
logger = Logger()
