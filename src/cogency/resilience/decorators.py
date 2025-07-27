"""Agent decorator implementations - Definitive composition of resilience + checkpointing."""

from functools import wraps

from resilient_result import Retry
from resilient_result import resilient as resilient_decorator

from cogency.resilience.checkpoint import checkpoint


def _checkpoint(name: str, interruptible: bool = True):
    """Context-driven checkpointing wrapper - applies only when task_id exists."""

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract state from function arguments
            state = args[0] if args else kwargs.get("state")

            # Apply checkpointing only when task context exists
            if hasattr(state, "context") and hasattr(state.context, "task_id"):
                checkpointed = checkpoint(name, interruptible=interruptible)(func)
                return await checkpointed(*args, **kwargs)

            # No checkpointing overhead for non-task contexts
            return await func(*args, **kwargs)

        return wrapper

    return decorator


def _policy(checkpoint_name: str, interruptible: bool = True, default_retry=None):
    """Universal agent policy factory - composes resilience + context-driven checkpointing."""

    def policy(retry=None, **kwargs):
        retry = retry or default_retry or Retry.api()

        def decorator(func):
            # 1. Apply resilience
            resilient_func = resilient_decorator(retry=retry)(func)

            # 2. Apply context-driven checkpointing
            checkpointed_func = _checkpoint(checkpoint_name, interruptible)(resilient_func)

            return checkpointed_func

        return decorator

    return policy


# Domain-specific policies with smart defaults
reason = _policy("reasoning", interruptible=True, default_retry=Retry.api())
act = _policy("tool_execution", interruptible=True, default_retry=Retry.db())
preprocess = _policy(
    "preprocessing", interruptible=False, default_retry=Retry(attempts=2, timeout=10.0)
)
respond = _policy("response", interruptible=False, default_retry=Retry(attempts=2, timeout=15.0))


# Generic policy for one-off use cases
generic = _policy("generic", interruptible=True)


class _RobustDecorators:
    """Clean decorator factory for robust behaviors."""

    reason = staticmethod(reason)
    act = staticmethod(act)
    preprocess = staticmethod(preprocess)
    respond = staticmethod(respond)
    generic = staticmethod(generic)


robust = _RobustDecorators()

__all__ = ["robust", "reason", "act", "preprocess", "respond", "generic"]
