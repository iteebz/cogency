"""Beautiful error handling - reads like English.
@safe.tools    - Tool execution with recovery
@safe.reasoning - LLM reasoning with fallback
@safe.parsing  - JSON parsing with correction
@safe.memory   - Memory ops with graceful degradation
"""

import asyncio
from functools import wraps
from typing import Any, AsyncGenerator, Callable


class Safe:
    """Beautiful @safe decorators that read like English."""

    @staticmethod
    def _base_decorator(recovery_fn: Callable = None, max_retries: int = 3):
        """Base decorator with optional recovery function."""

        def decorator(func):
            if func.__name__ == "stream":

                @wraps(func)
                async def safe_stream(*args, **kwargs) -> AsyncGenerator[Any, None]:
                    for attempt in range(max_retries):
                        try:
                            async for chunk in func(*args, **kwargs):
                                yield chunk
                            return
                        except Exception as e:
                            if recovery_fn and attempt < max_retries - 1:
                                recovery_result = await recovery_fn(e, *args, **kwargs)
                                if recovery_result and recovery_result.success:
                                    continue
                            if attempt == max_retries - 1:
                                yield f"Stream error: {str(e)}"
                                return
                            await asyncio.sleep(2**attempt * 0.5)

                return safe_stream
            else:

                @wraps(func)
                async def safe_run(*args, **kwargs) -> Any:
                    for attempt in range(max_retries):
                        try:
                            return await func(*args, **kwargs)
                        except Exception as e:
                            if recovery_fn and attempt < max_retries - 1:
                                recovery_result = await recovery_fn(e, *args, **kwargs)
                                if recovery_result and recovery_result.success:
                                    return recovery_result.data
                            if attempt == max_retries - 1:
                                return f"Error: {str(e)}"
                            await asyncio.sleep(2**attempt * 0.5)

                return safe_run

        return decorator

    @classmethod
    def tools(cls, max_retries: int = 2):
        """@safe.tools - Tool execution with network retry."""

        async def recover_tool_error(error, *args, **kwargs):
            from cogency.utils.results import RecoveryResult

            error_str = str(error).lower()
            if any(word in error_str for word in ["timeout", "network", "connection"]):
                return RecoveryResult.ok(None, recovery_action="retry_network")
            return RecoveryResult.fail(str(error))

        return cls._base_decorator(recover_tool_error, max_retries)

    @classmethod
    def reasoning(cls, max_retries: int = 3):
        """@safe.reasoning - LLM reasoning with mode fallback."""

        async def recover_reasoning_error(error, *args, **kwargs):
            from cogency.utils.results import RecoveryResult

            # Fallback to fast mode if available in state
            if len(args) > 0 and hasattr(args[0], "react_mode") and args[0].react_mode == "deep":
                args[0].react_mode = "fast"
                return RecoveryResult.ok(None, recovery_action="fallback_fast_mode")
            return RecoveryResult.fail(str(error))

        return cls._base_decorator(recover_reasoning_error, max_retries)

    @classmethod
    def parsing(cls, max_retries: int = 2):
        """@safe.parsing - JSON parsing with correction."""

        async def recover_parsing_error(error, *args, **kwargs):
            from cogency.utils.results import RecoveryResult

            # This will integrate with existing parse_json_with_correction
            return RecoveryResult.fail(str(error))  # Let parse_json_with_correction handle it

        return cls._base_decorator(recover_parsing_error, max_retries)

    @classmethod
    def llm(cls, max_retries: int = 3):
        """@safe.llm - LLM calls with network retry."""

        async def recover_llm_error(error, *args, **kwargs):
            from cogency.utils.results import RecoveryResult

            # Network retry for LLM failures
            return RecoveryResult.fail(str(error))  # Basic retry handled by base decorator

        return cls._base_decorator(recover_llm_error, max_retries)

    @classmethod
    def memory(cls, max_retries: int = 1):
        """@safe.memory - Memory ops with graceful degradation."""

        async def recover_memory_error(error, *args, **kwargs):
            from cogency.utils.results import RecoveryResult

            # Continue without memory on failure
            return RecoveryResult.ok({}, recovery_action="disable_memory")

        return cls._base_decorator(recover_memory_error, max_retries)


# Create singleton instance for beautiful usage
safe = Safe()
