import logging
import sys

logger = logging.getLogger("cogency")
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


def set_debug(enabled: bool = True):
    logger.setLevel(logging.DEBUG if enabled else logging.INFO)
