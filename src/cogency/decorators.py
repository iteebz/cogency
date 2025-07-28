"""Agent decorator implementations - Definitive composition of resilience + checkpointing."""

from functools import wraps

from resilient_result import Retry
from resilient_result import resilient as resilient_decorator

from cogency.resilience.checkpoint import checkpoint
from cogency.monitoring.metrics import timer, counter, histogram

# Global flag for toggleable robust behavior
_robust_enabled = True  # Default enabled

# Global flag for toggleable observability behavior
_observe_enabled = False  # Default disabled - opt-in for production metrics

# Global persistence manager - set by Agent during initialization
_persistence_manager = None


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
            
            # Auto-save state after successful completion
            if _persistence_manager and _persistence_manager.enabled:
                try:
                    # Extract state from function arguments
                    state = args[0] if args else kwargs.get("state")
                    if state and hasattr(state, 'user_id'):
                        # Extract LLM info from kwargs for validation
                        llm = kwargs.get('llm') or (args[1] if len(args) > 1 else None)
                        tools = kwargs.get('tools') or (args[2] if len(args) > 2 else None)
                        
                        await _persistence_manager.save_state(
                            state,
                            llm_provider=getattr(llm, 'provider', 'unknown') if llm else 'unknown',
                            llm_model=getattr(llm, 'model', 'unknown') if llm else 'unknown',
                            tools_count=len(tools) if tools else 0,
                            memory_backend='unknown',  # Could extract from memory backend
                            phase_completed=phase_name
                        )
                except Exception:
                    # Graceful degradation - don't break agent execution on persistence failure
                    pass
            
            return result
        return wrapper
    return decorator


def _observe_metrics(phase_name: str):
    """Observability wrapper - metrics collection and timing for phase operations."""
    
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Check global observe flag
            if not _observe_enabled:
                # Pass-through decorator - no observability overhead
                return await func(*args, **kwargs)
            
            # Extract state for context tags (prioritize kwargs, fallback to args[0])
            state = kwargs.get("state") or (args[0] if args else None)
            tags = {
                "phase": phase_name,
                "iteration": str(getattr(state, "iteration", 0)) if state else "0",
                "react_mode": getattr(state, "react_mode", "unknown") if state else "unknown"
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
                    if result and hasattr(result, '__len__'):
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
            # Check global robust flag
            if not _robust_enabled:
                # Pass-through decorator - no resilience or checkpointing  
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


# Domain-specific policies with smart defaults
reason = _policy("reasoning", interruptible=True, default_retry=Retry.api())
act = _policy("tool_execution", interruptible=True, default_retry=Retry.db())
preprocess = _policy(
    "preprocessing", interruptible=False, default_retry=Retry(attempts=2, timeout=10.0)
)
respond = _policy("response", interruptible=False, default_retry=Retry(attempts=2, timeout=15.0))


# Generic policy for one-off use cases
generic = _policy("generic", interruptible=True)

# Observability decorators - phase-specific telemetry collection
observe_reason = _observe_policy("reasoning")
observe_act = _observe_policy("tool_execution") 
observe_preprocess = _observe_policy("preprocessing")
observe_respond = _observe_policy("response")
observe_generic = _observe_policy("generic")


class _RobustDecorators:
    """Clean decorator factory for robust behaviors."""

    reason = staticmethod(reason)
    act = staticmethod(act)
    preprocess = staticmethod(preprocess)
    respond = staticmethod(respond)
    generic = staticmethod(generic)


class _ObserveDecorators:
    """Clean decorator factory for observability behaviors."""

    reason = staticmethod(observe_reason)
    act = staticmethod(observe_act)
    preprocess = staticmethod(observe_preprocess)
    respond = staticmethod(observe_respond)
    generic = staticmethod(observe_generic)


robust = _RobustDecorators()
observe = _ObserveDecorators()


def is_robust_enabled() -> bool:
    """Check if robust decorators are enabled."""
    return _robust_enabled


def is_observe_enabled() -> bool:
    """Check if observe decorators are enabled."""
    return _observe_enabled


def set_observe_enabled(enabled: bool) -> None:
    """Enable or disable observability decorators globally."""
    global _observe_enabled
    _observe_enabled = enabled


def set_persistence_manager(manager):
    """Set global persistence manager for auto-save functionality."""
    global _persistence_manager
    _persistence_manager = manager


def get_persistence_manager():
    """Get current persistence manager."""
    return _persistence_manager


__all__ = [
    "robust", "reason", "act", "preprocess", "respond", "generic", "is_robust_enabled", 
    "observe", "is_observe_enabled", "set_observe_enabled",
    "set_persistence_manager", "get_persistence_manager"
]
