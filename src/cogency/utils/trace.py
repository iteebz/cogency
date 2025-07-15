"""Clean trace decorator with safe serialization."""
from functools import wraps
from copy import deepcopy
from cogency.utils.diff import compute_diff, generate_trace_message


def _safe_deepcopy(obj):
    """Safe deepcopy that handles unpicklable objects."""
    try:
        return deepcopy(obj)
    except (TypeError, AttributeError) as e:
        # Handle unpicklable objects like SimpleQueue
        if hasattr(obj, '__dict__'):
            safe_dict = {}
            for k, v in obj.__dict__.items():
                try:
                    safe_dict[k] = deepcopy(v)
                except (TypeError, AttributeError):
                    safe_dict[k] = f"<unpicklable: {type(v).__name__}>"
            return safe_dict
        else:
            return f"<unpicklable: {type(obj).__name__}>"


def trace_node(node_name: str):
    """Decorator that adds tracing via post-hoc state diff analysis."""
    def decorator(fn):
        @wraps(fn)
        async def wrapped(state, *args, **kwargs):
            # Take safe snapshot before execution
            before = _safe_deepcopy(state)
            
            # Execute pure business logic
            result = await fn(state, *args, **kwargs)
            
            # Take safe snapshot after execution
            after = _safe_deepcopy(result)
            
            # Compute diff and generate trace message
            delta = compute_diff(before, after)
            message = generate_trace_message(node_name, delta)
            
            # Add to trace if present
            if state.get("trace"):
                state["trace"].add(node_name, message, delta)
            
            return result
        return wrapped
    return decorator


# Alias for backward compatibility
trace = trace_node