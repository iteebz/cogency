"""User profile context injection and direct memory integration.

CANONICAL LOCATION: cogency.memory
This module re-exports for backward compatibility during refactoring.
"""

# Re-export canonical implementations from memory domain
from cogency.memory.memory import MemoryManager as Memory
from cogency.memory.memory import Profile

__all__ = ["Memory", "Profile"]
