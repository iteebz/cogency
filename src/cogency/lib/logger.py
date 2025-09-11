"""Simple logging interface."""

import logging
import sys

# Configure logger once
logger = logging.getLogger("cogency")
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


def set_debug(enabled: bool = True):
    """Enable/disable debug logging."""
    logger.setLevel(logging.DEBUG if enabled else logging.INFO)
