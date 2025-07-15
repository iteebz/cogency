"""Clean trace decorator with post-hoc diff analysis."""
from functools import wraps
from copy import deepcopy
from cogency.utils.diff import compute_diff, generate_trace_message


def trace_node(node_name: str):
    """Decorator that adds tracing via post-hoc state diff analysis."""
    def decorator(fn):
        @wraps(fn)
        async def wrapped(state, *args, **kwargs):
            # Take snapshot before execution
            before = deepcopy(state)
            
            # Execute pure business logic
            result = await fn(state, *args, **kwargs)
            
            # Take snapshot after execution
            after = deepcopy(result)
            
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