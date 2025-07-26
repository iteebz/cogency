"""Domain-specific resilience patterns for Cogency.
World-class resilience with AI agent specific recovery patterns using resilient-result.
"""

import asyncio
import signal
from contextlib import asynccontextmanager
from functools import wraps

from resilient_result import Result, resilient


def unwrap_result(result):
    """Centralized Result unwrapping logic - maintains clean State boundary."""
    if isinstance(result, Result):
        if result.success:
            return result.data
        else:
            raise result.error
    return result


@asynccontextmanager
async def interruptible_context():
    """Context manager for proper async signal handling."""
    interrupted = asyncio.Event()
    current_task = asyncio.current_task()

    def signal_handler():
        interrupted.set()
        if current_task:
            current_task.cancel()

    # Use asyncio event loop signal handling
    loop = asyncio.get_running_loop()
    loop.add_signal_handler(signal.SIGINT, signal_handler)

    try:
        yield interrupted
    finally:
        # Clean up signal handler
        loop.remove_signal_handler(signal.SIGINT)


def state_aware_handler(unwrap_state: bool = True):
    """Create a handler that properly manages State objects."""

    async def handler(error, func, args, kwargs):
        """Handle State-specific errors with domain knowledge."""
        # For State operations, we can add specific recovery logic here
        # For now, just retry
        return None  # Trigger retry

    return handler


def state_aware(handler=None, retries: int = 3, unwrap_state: bool = True, **kwargs):
    """State-aware decorator using resilient-result as base."""

    # Use state-aware handler if none provided
    if handler is None:
        handler = state_aware_handler(unwrap_state)

    return resilient(handler=handler, retries=retries, **kwargs)


# Domain-specific recovery patterns for AI agents


def reasoning(retries: int = 3, unwrap_state: bool = True):
    """@resilient.reasoning - LLM reasoning with mode fallback."""

    def decorator(func):
        # State-aware handler using closure to access args
        async def handle_reasoning(error):
            # Access args through closure from wrapper
            if (
                hasattr(handle_reasoning, "_current_args")
                and len(handle_reasoning._current_args) > 0
                and hasattr(handle_reasoning._current_args[0], "react_mode")
                and handle_reasoning._current_args[0].react_mode == "deep"
            ):
                handle_reasoning._current_args[0].react_mode = "fast"
                return None  # Retry with modified state
            return False  # No recovery possible

        # Get resilient decorator
        resilient_func = resilient(handler=handle_reasoning, retries=retries)(func)

        if not unwrap_state:

            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Store args for handler access
                handle_reasoning._current_args = args
                try:
                    return await resilient_func(*args, **kwargs)
                finally:
                    # Clean up
                    if hasattr(handle_reasoning, "_current_args"):
                        delattr(handle_reasoning, "_current_args")

            return wrapper
        else:

            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Store args for handler access
                handle_reasoning._current_args = args
                try:
                    result = await resilient_func(*args, **kwargs)
                    return unwrap_result(result)
                finally:
                    # Clean up
                    if hasattr(handle_reasoning, "_current_args"):
                        delattr(handle_reasoning, "_current_args")

            return wrapper

    return decorator


def memory(retries: int = 1, unwrap_state: bool = True):
    """@resilient.memory - Memory ops with graceful degradation."""

    async def handle_memory(error):
        return None  # Retry memory errors

    def decorator(func):
        # Get the resilient decorator
        resilient_func = resilient(handler=handle_memory, retries=retries)(func)

        if not unwrap_state:
            return resilient_func

        @wraps(func)
        async def wrapper(*args, **kwargs):
            result = await resilient_func(*args, **kwargs)
            # Transparently unwrap Result objects to maintain State interface
            return unwrap_result(result)

        return wrapper

    return decorator


def act(retries: int = 2, unwrap_state: bool = True):
    """@resilient.act - Tool execution with domain-specific recovery."""

    async def handle_act(error):
        return None  # Retry action errors

    def decorator(func):
        # Get the resilient decorator
        resilient_func = resilient(handler=handle_act, retries=retries)(func)

        if not unwrap_state:
            return resilient_func

        @wraps(func)
        async def wrapper(*args, **kwargs):
            result = await resilient_func(*args, **kwargs)
            # Transparently unwrap Result objects to maintain State interface
            return unwrap_result(result)

        return wrapper

    return decorator


def checkpoint(checkpoint_type: str = "tool_execution", interruptible: bool = False):
    """@safe.checkpoint - Workflow recovery with state persistence."""

    async def recover_checkpoint_error(error, *args, **kwargs):
        from cogency.utils.results import RecoveryResult

        # Try to resume from existing checkpoint
        if args and hasattr(args[0], "get"):
            state = args[0]
            from .checkpoint import checkpoints

            checkpoint_id = checkpoints.find_checkpoint(state)
            if checkpoint_id:
                checkpoint_data = checkpoints.load_checkpoint(checkpoint_id)
                if checkpoint_data:
                    return RecoveryResult.ok(
                        checkpoint_data,
                        recovery_action=f"resume_checkpoint_{checkpoint_id[:8]}",
                    )

        return RecoveryResult.fail(str(error))

    def decorator(func):
        @wraps(func)
        async def checkpointed_func(*args, **kwargs):
            # Check for existing checkpoint before execution
            if args and hasattr(args[0], "get"):
                state = args[0]
                from .checkpoint import checkpoints

                checkpoint_id = checkpoints.find_checkpoint(state)
                if checkpoint_id and state.get("resume_from_checkpoint"):
                    # Resume from checkpoint
                    checkpoint_data = checkpoints.load_checkpoint(checkpoint_id)
                    if checkpoint_data:
                        # Restore state from checkpoint
                        for key, value in checkpoint_data.items():
                            if key not in ["fingerprint", "timestamp", "checkpoint_type"]:
                                state[key] = value
                        return state

            # Execute with proper interrupt handling if enabled
            if interruptible:
                async with interruptible_context() as interrupted:
                    try:
                        task = asyncio.create_task(func(*args, **kwargs))
                        result = await task

                        # Save checkpoint after successful execution
                        if (
                            args
                            and hasattr(args[0], "get")
                            and checkpoint_type in ["preprocess", "reason", "act", "respond"]
                        ):
                            state = args[0]
                            from .checkpoint import checkpoints

                            checkpoints.save_checkpoint(state, checkpoint_type)

                        return result

                    except asyncio.CancelledError:
                        # Signal handler cancelled the task - save checkpoint
                        if interrupted.is_set() and args and hasattr(args[0], "get"):
                            state = args[0]
                            from .checkpoint import checkpoints

                            checkpoints.save_checkpoint(state, f"{checkpoint_type}_interrupted")
                        raise  # Let CancelledError propagate naturally

                    except Exception as e:
                        # Save checkpoint on failure
                        if args and hasattr(args[0], "get"):
                            state = args[0]
                            from .checkpoint import checkpoints

                            checkpoints.save_checkpoint(state, f"{checkpoint_type}_failed")

                        # Attempt recovery via checkpoint
                        recovery_result = await recover_checkpoint_error(e, *args, **kwargs)
                        if recovery_result and recovery_result.success:
                            # Restore state from checkpoint data and return State object
                            state = args[0]
                            checkpoint_data = recovery_result.data
                            for key, value in checkpoint_data.items():
                                if key not in ["fingerprint", "timestamp", "checkpoint_type"]:
                                    state[key] = value
                            return state
                        raise
            else:
                # Execute normally without interrupt handling
                try:
                    result = await func(*args, **kwargs)

                    # Save checkpoint after successful execution
                    if (
                        args
                        and hasattr(args[0], "get")
                        and checkpoint_type in ["preprocess", "reason", "act", "respond"]
                    ):
                        state = args[0]
                        from .checkpoint import checkpoints

                        checkpoints.save_checkpoint(state, checkpoint_type)

                    return result
                except Exception as e:
                    # Save checkpoint on failure
                    if args and hasattr(args[0], "get"):
                        state = args[0]
                        from .checkpoint import checkpoints

                        checkpoints.save_checkpoint(state, f"{checkpoint_type}_failed")

                    # Attempt recovery via checkpoint
                    recovery_result = await recover_checkpoint_error(e, *args, **kwargs)
                    if recovery_result and recovery_result.success:
                        # Restore state from checkpoint data and return State object
                        state = args[0]
                        checkpoint_data = recovery_result.data
                        for key, value in checkpoint_data.items():
                            if key not in ["fingerprint", "timestamp", "checkpoint_type"]:
                                state[key] = value
                        return state
                    raise

        return checkpointed_func

    return decorator


# Register Cogency patterns with resilient-result
resilient.register("reasoning", reasoning)
resilient.register("memory", memory)
resilient.register("act", act)


# Create Cogency-specific safe instance that extends resilient-result
class CogencySafe:
    """Cogency-specific resilience patterns built on resilient-result."""

    def __call__(self, *args, **kwargs):
        """Direct decorator usage - delegates to resilient-result."""
        return resilient(*args, **kwargs)

    def __getattr__(self, name: str):
        """Auto-discover patterns from resilient-result registry."""
        return getattr(resilient, name)

    # Complex patterns that don't fit the standard registry pattern
    def checkpoint(self, checkpoint_type: str = "tool_execution", interruptible: bool = False):
        """@safe.checkpoint - Workflow recovery with state persistence."""
        return globals()["checkpoint"](checkpoint_type, interruptible)


# Beautiful global instance
safe = CogencySafe()
