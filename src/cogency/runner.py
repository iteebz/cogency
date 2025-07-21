"""Clean flow execution - no streaming concerns."""
from typing import Dict, Any, Callable, Awaitable
from cogency.state import State


class FlowRunner:
    """Pure flow execution - no streaming, no tracing concerns."""
    
    async def execute(
        self, 
        flow, 
        state: State, 
        stream_cb: Callable[[str], Awaitable[None]] = None
    ) -> State:
        """Execute flow with optional streaming callback."""
        if stream_cb:
            state.output.callback = stream_cb
        
        return await flow.ainvoke(state)


class StreamRunner:
    """Streaming wrapper for user-facing Chain-of-Thought."""
    
    def __init__(self):
        self.runner = FlowRunner()
    
    async def stream(self, flow, state: State, stream_cb: Callable[[str], Awaitable[None]]):
        """Execute flow with streaming callback for user updates."""
        return await self.runner.execute(flow, state, stream_cb)