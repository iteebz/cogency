"""Domain-specific @safe plugins for Cogency.
Extends resilient-result with AI agent specific recovery patterns.
"""

import asyncio
import signal
from contextlib import asynccontextmanager
from functools import wraps

from resilient_result import resilient as base_resilient

from cogency.state import State


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


def state_aware_decorator(handler=None, retries: int = 3, unwrap_state: bool = True, **kwargs):
    """Decorator that handles State objects properly - can unwrap them from Result objects."""
    from resilient_result import Result
    from resilient_result.resilient import decorator as base_decorator

    def wrapper(func):
        # Apply the base resilient decorator
        resilient_func = base_decorator(handler=handler, retries=retries, **kwargs)(func)

        @wraps(func)
        async def state_unwrapper(*args, **kwargs):
            result = await resilient_func(*args, **kwargs)

            # If unwrap_state is False, return the Result object as-is
            if not unwrap_state:
                return result

            # If the result is a Result object containing a State, unwrap it
            if isinstance(result, Result):
                if result.success and isinstance(result.data, State):
                    return result.data
                elif not result.success:
                    # For failures, we still need to handle them appropriately
                    # In cogency, we typically want to raise the exception
                    if isinstance(result.error, Exception):
                        raise result.error
                    else:
                        raise Exception(str(result.error))

            return result

        return state_unwrapper

    return wrapper


# Domain-specific recovery patterns for AI agents


def reasoning(retries: int = 3, unwrap_state: bool = True):
    """@safe.reasoning - LLM reasoning with mode fallback."""

    def create_handler(func_args, func_kwargs):
        async def handle_reasoning(error):
            # Fallback to fast mode if available in state - this is actual recovery
            if (
                len(func_args) > 0
                and hasattr(func_args[0], "react_mode")
                and func_args[0].react_mode == "deep"
            ):
                func_args[0].react_mode = "fast"
                return None  # Retry with modified state
            return False  # No recovery possible

        return handle_reasoning

    def wrapper(func):
        @wraps(func)
        async def reasoning_wrapper(*args, **kwargs):
            # Create handler with access to function arguments
            handler = create_handler(args, kwargs)
            # Apply the state_aware_decorator with the handler
            decorated_func = state_aware_decorator(
                handler=handler, retries=retries, unwrap_state=unwrap_state
            )(func)
            return await decorated_func(*args, **kwargs)

        return reasoning_wrapper

    return wrapper


def memory(retries: int = 1, unwrap_state: bool = True):
    """@safe.memory - Memory ops with graceful degradation."""

    async def handle_memory(error):
        return None  # Retry memory errors

    return state_aware_decorator(handler=handle_memory, retries=retries, unwrap_state=unwrap_state)


def act(retries: int = 2, unwrap_state: bool = True):
    """@safe.act - Tool execution with domain-specific recovery."""

    async def handle_act(error):
        return None  # Retry action errors

    return state_aware_decorator(handler=handle_act, retries=retries, unwrap_state=unwrap_state)


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


# Create enhanced safe instance with domain plugins
safe = base_resilient
safe.reasoning = reasoning
safe.memory = memory
safe.act = act
safe.checkpoint = checkpoint
