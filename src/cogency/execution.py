"""Clean workflow execution - no streaming concerns."""
from typing import Dict, Any, Callable, Awaitable
from cogency.types import AgentState


class WorkflowExecutor:
    """Pure workflow execution - no streaming, no tracing concerns."""
    
    async def execute(
        self, 
        workflow, 
        state: AgentState, 
        streaming_callback: Callable[[str], Awaitable[None]] = None
    ) -> AgentState:
        """Execute workflow with optional streaming callback."""
        config = {}
        if streaming_callback:
            config = {"configurable": {"streaming_callback": streaming_callback}}
        
        return await workflow.ainvoke(state, config=config)


class StreamingExecutor:
    """Streaming wrapper for user-facing Chain-of-Thought."""
    
    def __init__(self):
        self.executor = WorkflowExecutor()
    
    async def stream_execute(self, workflow, state: AgentState, callback: Callable[[str], Awaitable[None]]):
        """Execute workflow with streaming callback for user updates."""
        return await self.executor.execute(workflow, state, callback)