import itertools
from typing import List


class KeyRotator:
    """Simple key rotator for API rate limit avoidance."""

    def __init__(self, keys: List[str]):
        self.keys = keys
        self.cycle = itertools.cycle(keys)

    def get_key(self) -> str:
        """Get next key in rotation."""
        return next(self.cycle)
