"""Memory and contextual understanding.

This module provides memory capabilities for agents to maintain context across
interactions. Memory components are internal implementation details and should
not be accessed directly.

For memory access: Use Agent.memory() method
For memory configuration: Use MemoryConfig in Agent setup

Internal components:
- SituatedMemory: Core memory component for profile context injection
- ArchivalMemory: Knowledge artifact storage and retrieval
- compress, extract_impressions: Memory processing utilities
"""

# Internal memory components - not exported
from .situated import SituatedMemory  # noqa: F401

# Internal functions not exported:
# from .compression import compress
# from .insights import extract_impressions

# No public exports - use Agent.memory() instead
__all__ = []
