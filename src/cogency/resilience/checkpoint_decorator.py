"""Checkpoint decorator for workflow recovery - focused and clean."""

import asyncio
from functools import wraps
from .utils import interruptible_context


def checkpoint(checkpoint_type: str = "tool_execution", interruptible: bool = False):
    """@safe.checkpoint - Workflow recovery with state persistence."""

    async def recover_checkpoint_error(error, *args, **kwargs):
        from cogency.utils.results import RecoveryResult

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
                    checkpoint_data = checkpoints.load_checkpoint(checkpoint_id)
                    if checkpoint_data:
                        for key, value in checkpoint_data.items():
                            if key not in ["fingerprint", "timestamp", "checkpoint_type"]:
                                state[key] = value
                        return state

            # Execute with proper interrupt handling if enabled
            if interruptible:
                async with interruptible_context() as interrupted:
                    return await _execute_with_checkpoints(
                        func, args, kwargs, checkpoint_type, interrupted
                    )
            else:
                return await _execute_with_checkpoints(func, args, kwargs, checkpoint_type)

        return checkpointed_func
    return decorator


async def _execute_with_checkpoints(func, args, kwargs, checkpoint_type, interrupted=None):
    """Execute function with checkpoint handling - DRY extraction."""
    try:
        if interrupted:
            task = asyncio.create_task(func(*args, **kwargs))
            result = await task
        else:
            result = await func(*args, **kwargs)

        # Save checkpoint after successful execution
        if (args and hasattr(args[0], "get") 
            and checkpoint_type in ["preprocess", "reason", "act", "respond"]):
            _save_checkpoint(args[0], checkpoint_type)
        return result

    except asyncio.CancelledError:
        if interrupted and interrupted.is_set() and args and hasattr(args[0], "get"):
            _save_checkpoint(args[0], f"{checkpoint_type}_interrupted")
        raise

    except Exception as e:
        if args and hasattr(args[0], "get"):
            _save_checkpoint(args[0], f"{checkpoint_type}_failed")

        recovery_result = await recover_checkpoint_error(e, *args, **kwargs)
        if recovery_result and recovery_result.success:
            state = args[0]
            checkpoint_data = recovery_result.data
            for key, value in checkpoint_data.items():
                if key not in ["fingerprint", "timestamp", "checkpoint_type"]:
                    state[key] = value
            return state
        raise


def _save_checkpoint(state, checkpoint_type):
    """Save checkpoint helper - DRY extraction."""
    from .checkpoint import checkpoints
    checkpoints.save_checkpoint(state, checkpoint_type)