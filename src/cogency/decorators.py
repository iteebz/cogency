"""Agent @step decorator - Unified composition of resilience + checkpointing + observability."""

from dataclasses import dataclass
from functools import wraps
from typing import Any, Optional

from resilient_result import Retry, resilient

# Metrics removed - agent observability handled by event system
from cogency.robust import checkpoint


def _retry_progress_handler(error: Exception) -> None:
    """Progress handler for retry visibility during development."""
    import logging

    logger = logging.getLogger(__name__)
    logger.debug(f"🔄 Retry: {type(error).__name__}: {error}")
    return None  # Continue retrying


@dataclass
class StepConfig:
    """Configuration state for step decorators - injected by Agent at runtime."""

    robust: Optional[Any] = None
    observe: Optional[Any] = None
    persist: Optional[Any] = None


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


def _auto_save(step_name: str, config: Optional[StepConfig] = None):
    """Auto-save state after successful step completion."""

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Execute the step
            result = await func(*args, **kwargs)

            # Auto-save only if persistence is configured and step succeeded
            if config and config.persist and result:
                try:
                    state = args[0] if args else kwargs.get("state")
                    if state:
                        # Handle both Persist config and StatePersistence instance
                        persist_obj = config.persist
                        if hasattr(persist_obj, "save"):
                            # It's a StatePersistence instance
                            await persist_obj.save(state)
                        elif hasattr(persist_obj, "store") and persist_obj.enabled:
                            # It's a Persist config, need to get the StatePersistence instance
                            from cogency.persist.store.base import _setup_persist

                            persistence = _setup_persist(persist_obj)
                            if persistence:
                                await persistence.save(state)
                except Exception:
                    # Don't fail the step due to persistence issues
                    pass

            return result

        return wrapper

    return decorator


def _observe_metrics(step_name: str, config: Optional[StepConfig] = None):
    """Unified observability wrapper - single timing measurement shared across metrics and notifications."""

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Check if observability is enabled
            if not config or not config.observe:
                return await func(*args, **kwargs)

            # Observability handled by event system - no decorator metrics needed
            result = await func(*args, **kwargs)
            return result

        return wrapper

    return decorator


def _policy(
    checkpoint_name: str,
    interruptible: bool = True,
    default_retry=None,
    config: Optional[StepConfig] = None,
):
    """Universal agent policy factory - composes resilience + checkpointing + persistence."""

    def policy(retry=None, **kwargs):
        retry = retry or default_retry or Retry.api()

        def decorator(func):
            if not config or not config.robust:
                return func

            # 1. Apply resilience with progress visibility
            resilient_func = resilient(retry=retry, handler=_retry_progress_handler)(func)
            # 2. Apply context-driven checkpointing
            checkpointed_func = _checkpoint(checkpoint_name, interruptible)(resilient_func)
            # 3. Apply auto-save after successful completion
            persisted_func = _auto_save(checkpoint_name, config)(checkpointed_func)
            return persisted_func

        return decorator

    return policy


def _observe_policy(step_name: str, config: Optional[StepConfig] = None):
    """Observability policy factory - metrics and telemetry collection."""

    def policy(**kwargs):
        def decorator(func):
            # Apply observability instrumentation
            return _observe_metrics(step_name, config)(func)

        return decorator

    return policy


def _step_factory(
    step_name: str, interruptible: bool, default_retry, config: Optional[StepConfig] = None
):
    """Step decorator factory that combines robust + observe based on config."""

    def step_decorator(**kwargs):
        def decorator(func):
            # Start with the original function
            result_func = func

            # Apply robust behavior if enabled
            if config and config.robust:
                robust_policy = _policy(step_name, interruptible, default_retry, config)
                result_func = robust_policy(**kwargs)(result_func)

            # Apply observability if enabled
            if config and config.observe:
                observe_policy = _observe_policy(step_name, config)
                result_func = observe_policy(**kwargs)(result_func)

            return result_func

        return decorator

    return step_decorator


def step_decorators(config: Optional[StepConfig] = None):
    """Create step decorators with injected config - no global state."""

    class _StepDecorators:
        """Unified @step decorator."""

        reason = staticmethod(_step_factory("reasoning", True, Retry.api(), config))
        act = staticmethod(
            _step_factory("tool_execution", True, Retry(attempts=2, timeout=15.0), config)
        )
        triage = staticmethod(
            _step_factory("triaging", False, Retry(attempts=2, timeout=10.0), config)
        )
        respond = staticmethod(
            _step_factory("response", False, Retry(attempts=2, timeout=15.0), config)
        )
        generic = staticmethod(_step_factory("generic", True, None, config))

    return _StepDecorators()


def elapsed(**kwargs) -> float:
    """Get current step duration - simplified without timer injection."""
    return 0.0  # Timer injection removed - use event system for timing


# Main decorator instance
step = step_decorators()


__all__ = [
    "step",
    "step_decorators",
    "StepConfig",
    "elapsed",
]
