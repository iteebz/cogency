"""Clean flow execution - no streaming concerns."""
from typing import Dict, Any, Callable, Awaitable
from cogency.types import AgentState


class FlowRunner:
    """Pure flow execution - no streaming, no tracing concerns."""
    
    async def execute(
        self, 
        flow, 
        state: AgentState, 
        streaming_callback: Callable[[str], Awaitable[None]] = None
    ) -> AgentState:
        """Execute flow with optional streaming callback."""
        config = {}
        if streaming_callback:
            config = {"configurable": {"streaming_callback": streaming_callback}}
        
        return await flow.ainvoke(state, config=config)


class StreamingRunner:
    """Streaming wrapper for user-facing Chain-of-Thought."""
    
    def __init__(self):
        self.runner = FlowRunner()
    
    async def stream_execute(self, flow, state: AgentState, callback: Callable[[str], Awaitable[None]]):
        """Execute flow with streaming callback for user updates."""
        return await self.runner.execute(flow, state, callback)