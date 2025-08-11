"""Agent observability system - focused on agent metrics only."""

import logging
import time
from functools import wraps
from typing import Any, Callable

from .exporters import OpenTelemetry, Prometheus
from .handlers import get_metrics_handler
from .profiler import get_profiler, profile_async, profile_sync
from .timing import timer
from .tokens import cost, count

logger = logging.getLogger(__name__)


def observe(func: Callable) -> Callable:
    """Observe step execution with timing and token tracking."""

    @wraps(func)
    async def wrapper(*args, **kwargs) -> Any:
        step_name = func.__name__
        start_time = time.time()

        # Extract state for user context if available
        user_id = "unknown"
        if args and hasattr(args[0], "execution") and hasattr(args[0].execution, "user_id"):
            user_id = args[0].execution.user_id

        logger.info(
            f"Step started: {step_name}",
            extra={
                "step": step_name,
                "user_id": user_id,
                "event": "step_start",
                "timestamp": start_time,
            },
        )

        try:
            # Execute the step
            result = await func(*args, **kwargs)

            # Calculate duration
            duration = time.time() - start_time

            logger.info(
                f"Step completed: {step_name} ({duration:.3f}s)",
                extra={
                    "step": step_name,
                    "user_id": user_id,
                    "event": "step_complete",
                    "duration": duration,
                    "success": True,
                },
            )

            return result

        except Exception as error:
            duration = time.time() - start_time

            logger.error(
                f"Step failed: {step_name} ({duration:.3f}s) - {error}",
                extra={
                    "step": step_name,
                    "user_id": user_id,
                    "event": "step_error",
                    "duration": duration,
                    "success": False,
                    "error": str(error),
                },
            )

            raise

    return wrapper


__all__ = [
    "observe",
    "get_metrics_handler",
    "get_profiler",
    "profile_async",
    "profile_sync",
    "timer",
    "Prometheus",
    "OpenTelemetry",
    "cost",
    "count",
]
