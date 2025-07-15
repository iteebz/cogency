"""Clean trace decorator - EXTENSIBLE."""
from functools import wraps
from cogency.types import ExecutionTrace


def trace(func):
    """Clean trace decorator for nodes - auto-detects node name."""
    @wraps(func)
    async def wrapper(state, *args, **kwargs):
        # Auto-detect node name from function
        current_node = func.__name__
        
        # Get trace from state
        execution_trace = state.get("execution_trace")
        if execution_trace:
            # Add starting step
            execution_trace.add(current_node, f"Starting {current_node}")
            # Print the step immediately
            step = execution_trace.steps[-1]
            print(step)
        
        # Execute the wrapped function
        result = await func(state, *args, **kwargs)
        
        # Add completion trace
        if execution_trace:
            execution_trace.add(current_node, f"Completed {current_node}")
            # Print the completion step immediately
            step = execution_trace.steps[-1]
            print(step)
        
        # Return result
        return result
            
    return wrapper