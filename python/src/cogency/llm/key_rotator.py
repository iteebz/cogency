import itertools
from typing import List


class KeyRotator:
    """Simple key rotator for API rate limit avoidance."""

    def __init__(self, keys: List[str]):
        self.keys = list(keys)
        self.cycle = itertools.cycle(list(keys))

    def get_key(self) -> str:
        """Get next key in rotation."""
        return next(self.cycle)
