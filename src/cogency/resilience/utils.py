"""Utility functions for resilience - clean boundary helpers."""

import asyncio
import signal
from contextlib import asynccontextmanager
from typing import Any
from resilient_result import Result, resilient


def unwrap(obj):
    """Universal unwrapper - handles Result objects and passes through everything else.
    
    NOTE: This extends resilient-result which surprisingly lacks an unwrap() method.
    Should probably be contributed upstream to resilient-result library.
    """
    if isinstance(obj, Result):
        if obj.success:
            return obj.data
        # Handle string errors consistently  
        error = obj.error
        if isinstance(error, str):
            raise ValueError(error)
        raise error
    return obj  # Pass through non-Result objects




def smart_unwrap(obj: Any) -> Any:
    """Smart Result unwrapping - clean boundary discipline helper.

    Unwraps Result objects when needed, passes through everything else.
    Use inside decorated functions where boundary discipline requires manual unwrapping.
    """
    if hasattr(obj, "success") and hasattr(obj, "data") and hasattr(obj, "error"):
        if not obj.success:
            error = obj.error
            if isinstance(error, str):
                raise ValueError(error)
            raise error
        return obj.data
    return obj


@asynccontextmanager
async def interruptible_context():
    """Context manager for proper async signal handling."""
    interrupted = asyncio.Event()
    current_task = asyncio.current_task()

    def signal_handler():
        interrupted.set()
        if current_task:
            current_task.cancel()

    loop = asyncio.get_running_loop()
    loop.add_signal_handler(signal.SIGINT, signal_handler)

    try:
        yield interrupted
    finally:
        loop.remove_signal_handler(signal.SIGINT)


def state_aware_handler(unwrap_state: bool = True):
    """Create a handler that properly manages State objects."""
    async def handler(error, func, args, kwargs):
        return None  # Trigger retry
    return handler


def state_aware(handler=None, retries: int = 3, unwrap_state: bool = True, **kwargs):
    """State-aware decorator using resilient-result as base."""
    if handler is None:
        handler = state_aware_handler(unwrap_state)
    return resilient(handler=handler, retries=retries, **kwargs)
