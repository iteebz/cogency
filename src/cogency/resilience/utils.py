"""Utility functions for resilience - clean boundary helpers."""

import asyncio
import signal
from contextlib import asynccontextmanager

from resilient_result import resilient

# unwrap() now available from resilient-result v0.3.0


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
    from resilient_result import Retry

    if handler is None:
        handler = state_aware_handler(unwrap_state)
    return resilient(retry=Retry(attempts=retries), handler=handler, **kwargs)
