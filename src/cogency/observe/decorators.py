"""Instrumentation decorators for measuring execution."""

import time
from functools import wraps
from typing import Any, Callable


def observe(func: Callable) -> Callable:
    """Observe function execution with timing and events."""

    @wraps(func)
    async def wrapper(*args, **kwargs) -> Any:
        step_name = func.__name__
        start_time = time.time()

        # Extract user context if available
        user_id = "unknown"
        if args and hasattr(args[0], "user_id"):
            user_id = args[0].user_id

        from cogency.events import emit

        emit("observe", step=step_name, user_id=user_id, event="start", timestamp=start_time)

        try:
            result = await func(*args, **kwargs)
            duration = time.time() - start_time

            emit(
                "observe",
                step=step_name,
                user_id=user_id,
                event="complete",
                duration=duration,
                success=True,
            )

            return result

        except Exception as error:
            duration = time.time() - start_time

            emit(
                "observe",
                step=step_name,
                user_id=user_id,
                event="error",
                duration=duration,
                success=False,
                error=str(error),
            )

            raise

    return wrapper
