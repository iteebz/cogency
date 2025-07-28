"""Agent decorator implementations - Definitive composition of resilience + checkpointing."""

from functools import wraps

from resilient_result import Retry
from resilient_result import resilient as resilient_decorator

from cogency.resilience.checkpoint import checkpoint

# Global flag for toggleable robust behavior
_robust_enabled = True  # Default enabled

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


def is_robust_enabled() -> bool:
    """Check if robust decorators are enabled."""
    return _robust_enabled


def set_persistence_manager(manager):
    """Set global persistence manager for auto-save functionality."""
    global _persistence_manager
    _persistence_manager = manager


def get_persistence_manager():
    """Get current persistence manager."""
    return _persistence_manager


__all__ = ["robust", "reason", "act", "preprocess", "respond", "generic", "is_robust_enabled", "set_persistence_manager", "get_persistence_manager"]
