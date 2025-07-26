"""Beautiful, auto-magical resilience for Cogency - ZERO ceremony."""

from resilient_result import resilient
from .decorators import *
from .utils import state_aware
from .checkpoint_decorator import checkpoint


class CogencySafe:
    """Cogency-specific resilience patterns - auto-magical and extensible."""

    def __call__(self, *args, **kwargs):
        """Direct decorator usage - delegates to resilient-result."""
        return resilient(*args, **kwargs)

    def __getattr__(self, name: str):
        """Auto-discover patterns from resilient-result registry."""
        return getattr(resilient, name)

    def checkpoint(self, checkpoint_type: str = "tool_execution", interruptible: bool = False):
        """@safe.checkpoint - Workflow recovery with state persistence."""
        return checkpoint(checkpoint_type, interruptible)


# Beautiful global instance
safe = CogencySafe()
