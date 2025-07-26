"""AI agent-specific resilient decorators - ZERO ceremony, maximum elegance."""

from functools import wraps
from resilient_result import resilient


def _create_domain_decorator(handler_name: str, default_retries: int = 2):
    """DRY factory for domain decorators - eliminates all boilerplate."""
    
    def domain_decorator(retries: int = default_retries, unwrap_state: bool = True):
        async def handler(error):
            return None  # Retry domain errors
            
        def decorator(func):
            resilient_func = resilient(handler=handler, retries=retries)(func)
            
            if not unwrap_state:
                return resilient_func
                
            @wraps(func)
            async def wrapper(*args, **kwargs):
                from .utils import unwrap
                result = await resilient_func(*args, **kwargs)
                return unwrap(result)
            return wrapper
        return decorator
    return domain_decorator


def reasoning(retries: int = 3, unwrap_state: bool = True):
    """@resilient.reasoning - LLM reasoning with mode fallback."""
    
    def decorator(func):
        async def handle_reasoning(error):
            if (hasattr(handle_reasoning, "_current_args") 
                and len(handle_reasoning._current_args) > 0
                and hasattr(handle_reasoning._current_args[0], "react_mode")
                and handle_reasoning._current_args[0].react_mode == "deep"):
                handle_reasoning._current_args[0].react_mode = "fast"
                return None  # Retry with modified state
            return False  # No recovery possible
            
        resilient_func = resilient(handler=handle_reasoning, retries=retries)(func)
        
        @wraps(func)
        async def wrapper(*args, **kwargs):
            handle_reasoning._current_args = args
            try:
                result = await resilient_func(*args, **kwargs)
                if unwrap_state:
                    from .utils import unwrap
                    return unwrap(result)
                return result
            finally:
                if hasattr(handle_reasoning, "_current_args"):
                    delattr(handle_reasoning, "_current_args")
        return wrapper
    return decorator


# Auto-generated domain decorators - ZERO duplication
memory = _create_domain_decorator("memory", 1)
act = _create_domain_decorator("act", 2) 
preprocess = _create_domain_decorator("preprocess", 2)
respond = _create_domain_decorator("respond", 2)

# Alias
reason = reasoning


# Register with resilient-result
resilient.register("reasoning", reasoning)
resilient.register("reason", reason)
resilient.register("memory", memory)
resilient.register("act", act)
resilient.register("preprocess", preprocess)
resilient.register("respond", respond)