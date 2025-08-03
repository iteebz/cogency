"""Memory and impression synthesis.

This module provides memory capabilities for agents to maintain context across
interactions. Memory components are internal implementation details and should
not be accessed directly.

For memory access: Use Agent.memory() method
For memory configuration: Use MemoryConfig in Agent setup

Internal components:
- ImpressionSynthesizer: Core memory component for context synthesis
- compress, extract_insights: Memory processing utilities
"""

# Internal memory components - not exported
from .synthesizer import ImpressionSynthesizer  # noqa: F401

# Internal functions not exported:
# from .compression import compress
# from .insights import extract_insights

# No public exports - use Agent.memory() instead
__all__ = []
