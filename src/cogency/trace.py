"""Simple tracing for cognitive nodes."""

def trace_node(func):
    """Optional trace decorator - no-op if trace disabled."""
    async def wrapper(*args, **kwargs):
        # Extract AgentState from node args (first argument)
        state = args[0] if args else None
        if (isinstance(state, dict) and 
            state.get("execution_trace") and 
            hasattr(state["execution_trace"], "add_step")):
            
            # Simple trace - just record the node execution
            result = await func(*args, **kwargs)
            state["execution_trace"].add_step(
                node=func.__name__,
                input_data={"input": "executed"},
                output_data={"output": "completed"},
                reasoning=f"Node {func.__name__} executed"
            )
            return result
        else:
            # No tracing - just execute
            return await func(*args, **kwargs)
    
    return wrapper