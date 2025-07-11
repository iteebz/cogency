"""Simple execution trace for cogency agent."""

from typing import Any, Dict, Callable, TypeVar
from functools import wraps
from cogency.types import AgentState

F = TypeVar('F', bound=Callable[..., Any])

def trace_node(func: F) -> F:
    """
    Simple decorator to trace agent node execution input/output only.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Assume first arg is AgentState
        state = args[0] if args else kwargs.get('state')
        if not state or not isinstance(state, dict):
            return func(*args, **kwargs)
        
        # If no trace enabled, run normally
        if not state.get("execution_trace"):
            return func(*args, **kwargs)
        
        # Simple input capture
        input_data = {
            "task_complete": state.get("task_complete", False),
            "last_node": state.get("last_node")
        }
        
        # Execute function
        result = func(*args, **kwargs)
        
        # Simple output capture
        output_data = {}
        if isinstance(result, dict):
            output_data = {
                "task_complete": result.get("task_complete", False),
                "last_node": result.get("last_node")
            }
        
        # Add to trace
        state["execution_trace"].add_step(func.__name__, input_data, output_data, f"Executed {func.__name__}")
        
        return result
    
    return wrapper

