"""Agent @phase decorator - Unified composition of resilience + checkpointing + observability."""

from dataclasses import dataclass, replace
from functools import wraps
from typing import Any, Optional

from resilient_result import Retry
from resilient_result import resilient as resilient_decorator

from cogency.observe import counter, histogram, timer
from cogency.robust import checkpoint


@dataclass
class PhaseConfig:
    """Configuration state for phase decorators - injected by Agent at runtime."""

    robust: Optional[Any] = None
    observe: Optional[Any] = None
    persist: Optional[Any] = None


# Phase decorator configuration - injected by Agent
_config = PhaseConfig()


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


def _auto_save(phase_name: str):
    """Auto-save state after successful phase completion."""

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Execute the phase
            result = await func(*args, **kwargs)

            # Auto-save only if persistence is configured and phase succeeded
            if _config.persist and result:
                try:
                    state = args[0] if args else kwargs.get("state")
                    if state:
                        await _config.persist.save(state)
                except Exception:
                    # Don't fail the phase due to persistence issues
                    pass

            return result

        return wrapper

    return decorator


def _observe_metrics(phase_name: str):
    """Observability wrapper - metrics collection and timing for phase operations."""

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Check if observability is enabled
            if not _config.observe:
                # Pass-through decorator - no observability overhead
                return await func(*args, **kwargs)

            # Extract state for context tags (prioritize kwargs, fallback to args[0])
            state = kwargs.get("state") or (args[0] if args else None)
            tags = {
                "phase": phase_name,
                "iteration": str(getattr(state, "iteration", 0)) if state else "0",
                "mode": getattr(state, "mode", "unknown") if state else "unknown",
            }

            # Count phase executions
            counter(f"{phase_name}.executions", 1.0, tags)

            # Time the phase execution
            with timer(f"{phase_name}.duration", tags):
                try:
                    result = await func(*args, **kwargs)

                    # Success metrics
                    counter(f"{phase_name}.success", 1.0, tags)

                    # Result size metrics if applicable
                    if result and hasattr(result, "__len__"):
                        histogram(f"{phase_name}.result_size", len(str(result)), tags)

                    return result

                except Exception as e:
                    # Error metrics
                    error_tags = {**tags, "error_type": type(e).__name__}
                    counter(f"{phase_name}.errors", 1.0, error_tags)
                    raise

        return wrapper

    return decorator


def _policy(checkpoint_name: str, interruptible: bool = True, default_retry=None):
    """Universal agent policy factory - composes resilience + checkpointing + persistence."""

    def policy(retry=None, **kwargs):
        retry = retry or default_retry or Retry.api()

        def decorator(func):
            if not _config.robust:
                return func

            # 1. Apply resilience
            resilient_func = resilient_decorator(retry=retry)(func)
            # 2. Apply context-driven checkpointing
            checkpointed_func = _checkpoint(checkpoint_name, interruptible)(resilient_func)
            # 3. Apply auto-save after successful completion
            persisted_func = _auto_save(checkpoint_name)(checkpointed_func)
            return persisted_func

        return decorator

    return policy


def _observe_policy(phase_name: str):
    """Observability policy factory - metrics and telemetry collection."""

    def policy(**kwargs):
        def decorator(func):
            # Apply observability instrumentation
            return _observe_metrics(phase_name)(func)

        return decorator

    return policy


def _phase_factory(phase_name: str, interruptible: bool, default_retry):
    """Phase decorator factory that combines robust + observe based on config."""

    def phase_decorator(**kwargs):
        def decorator(func):
            # Start with the original function
            result_func = func

            # Apply robust behavior if enabled
            if _config.robust:
                robust_policy = _policy(phase_name, interruptible, default_retry)
                result_func = robust_policy(**kwargs)(result_func)

            # Apply observability if enabled
            if _config.observe:
                observe_policy = _observe_policy(phase_name)
                result_func = observe_policy(**kwargs)(result_func)

            return result_func

        return decorator

    return phase_decorator


class _PhaseDecorators:
    """Unified @phase decorator with beautiful IDE autocomplete."""

    reason = staticmethod(_phase_factory("reasoning", True, Retry.api()))
    act = staticmethod(_phase_factory("tool_execution", True, Retry.db()))
    preprocess = staticmethod(
        _phase_factory("preprocessing", False, Retry(attempts=2, timeout=10.0))
    )
    respond = staticmethod(_phase_factory("response", False, Retry(attempts=2, timeout=15.0)))
    generic = staticmethod(_phase_factory("generic", True, None))


# Export unified @phase constructor
phase = _PhaseDecorators()


def configure(robust=None, observe=None, persistence=None):
    """Configure @phase decorator behavior - called by Agent constructor."""
    _config.robust = robust
    _config.observe = observe
    _config.persist = persistence


def get_config():
    """Get current decorator configuration."""
    return replace(_config)


__all__ = [
    "phase",
    "configure",
    "get_config",
]
