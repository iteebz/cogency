"""Custom streaming wrapper for agent execution without LangGraph serialization issues."""
import asyncio
from typing import AsyncIterator, Dict, Any, Optional
from dataclasses import dataclass
from cogency.types import ExecutionTrace, AgentState


@dataclass
class StreamEvent:
    """Event emitted during streaming execution."""
    event_type: str  # "trace_update", "node_start", "node_end", "final_state"
    node: Optional[str] = None
    message: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    timestamp: Optional[float] = None


class StreamingExecutor:
    """Custom streaming wrapper that manages execution without serialization issues."""
    
    def __init__(self):
        self.event_queue: asyncio.Queue = asyncio.Queue()
        self.is_streaming = False
        self.final_state = None
        
    async def astream_execute(self, workflow, state: AgentState) -> AsyncIterator[StreamEvent]:
        """Execute workflow with streaming trace updates."""
        self.is_streaming = True
        self.final_state = None
        
        # Start execution in background task
        execution_task = asyncio.create_task(self._execute_workflow(workflow, state))
        
        try:
            # Yield events as they come
            while True:
                try:
                    # Wait for next event with timeout
                    event = await asyncio.wait_for(self.event_queue.get(), timeout=0.1)
                    yield event
                    
                    # Check if execution is complete
                    if event.event_type == "final_state":
                        self.final_state = event.data["state"]
                        break
                        
                except asyncio.TimeoutError:
                    # Check if execution task is done
                    if execution_task.done():
                        break
                    continue
                    
        finally:
            self.is_streaming = False
            # Ensure execution task completes
            if not execution_task.done():
                await execution_task
    
    async def _execute_workflow(self, workflow, state: AgentState):
        """Execute workflow and emit events."""
        try:
            # Hook into trace to capture updates
            original_trace = state.get("trace")
            if original_trace:
                original_trace._streaming_executor = self
            
            # Execute workflow
            final_state = await workflow.ainvoke(state)
            
            # Emit final state event
            await self.event_queue.put(StreamEvent(
                event_type="final_state",
                data={"state": final_state}
            ))
            
        except Exception as e:
            await self.event_queue.put(StreamEvent(
                event_type="error",
                data={"error": str(e)}
            ))
            raise
    
    async def emit_trace_update(self, node: str, message: str, data: Dict[str, Any] = None, timestamp: float = None):
        """Called by trace system to emit streaming updates."""
        if self.is_streaming:
            event = StreamEvent(
                event_type="trace_update",
                node=node,
                message=message,
                data=data or {},
                timestamp=timestamp
            )
            await self.event_queue.put(event)