"""Resilience and error recovery capabilities.

This module provides resilience features built on resilient-result:

- checkpoint: Decorator for checkpointing functions
- checkpointer: Checkpointing utility class
- resume: Function to resume from checkpoints
- recovery: Error recovery mechanisms

These capabilities enable agents to handle failures gracefully and resume
execution from known good states.
"""

# Import resilient-result for internal use only

from .checkpoint import checkpoint, checkpointer, resume
from .recovery import recovery

__all__ = [
    "checkpoint",
    "checkpointer",
    "resume",
    "recovery",
]
