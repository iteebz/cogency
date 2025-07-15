import itertools
from typing import List, Optional


class KeyRotator:
    """Simple key rotator for API rate limit avoidance."""

    def __init__(self, keys: List[str]):
        self.keys = list(keys)
        self.cycle = itertools.cycle(list(keys))
        self.current_key: Optional[str] = None

    def get_key(self) -> str:
        """Get next key in rotation."""
        self.current_key = next(self.cycle)
        return self.current_key
    
    def rotate_key(self) -> str:
        """Rotate to next key immediately. Returns feedback."""
        self.get_key()
        return "Rate limited, rotating to next key"
