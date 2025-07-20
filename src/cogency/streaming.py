"""Custom streaming wrapper for agent execution without LangGraph serialization issues."""
import asyncio
from typing import AsyncIterator, Dict, Any, Optional
from dataclasses import dataclass
from cogency.tracing import ExecutionTrace
from cogency.types import AgentState


@dataclass
class StreamEvent:
    """Event emitted during streaming execution."""
    event_type: str  # "trace_update", "node_start", "node_end", "final_state"
    node: Optional[str] = None
    message: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    timestamp: Optional[float] = None


class ExecutionStreamer:
    """Custom streaming wrapper that manages execution without serialization issues."""
    
    def __init__(self):
        self.event_queue: asyncio.Queue = asyncio.Queue()
        self.is_streaming = False
        self.final_state = None
        self._execution_task: Optional[asyncio.Task] = None
        
    async def astream_execute(self, workflow, state: AgentState) -> AsyncIterator[StreamEvent]:
        """Execute workflow with streaming trace updates."""
        self.is_streaming = True
        self.final_state = None
        
        # Start execution in background task
        self._execution_task = asyncio.create_task(self._execute_workflow(workflow, state))
        
        try:
            # Yield events as they come
            while True:
                try:
                    # Wait for next event with timeout
                    event = await asyncio.wait_for(self.event_queue.get(), timeout=1.0)
                    yield event
                    
                    # Check if execution is complete
                    if event.event_type == "final_state":
                        self.final_state = event.data["state"]
                        break
                    elif event.event_type == "error":
                        raise RuntimeError(event.data.get("error", "An unknown error occurred during streaming"))
                        
                except asyncio.CancelledError:
                    raise  # Re-raise CancelledError immediately
                except asyncio.TimeoutError:
                    # Check if execution task is done
                    if self._execution_task.done():
                        exc = self._execution_task.exception()
                        if isinstance(exc, asyncio.CancelledError):
                            raise exc  # Force propagation
                        elif exc:
                            raise exc
                        break
                    continue
                    
        finally:
            self.is_streaming = False
            # Ensure execution task completes and propagate exceptions
            if not self._execution_task.done():
                try:
                    await self._execution_task
                except asyncio.CancelledError:
                    raise  # Re-raise CancelledError immediately
                except Exception:
                    # Other exceptions are handled by the error event, but ensure task is awaited
                    pass
    
    async def _execute_workflow(self, workflow, state: AgentState):
        """Execute workflow and emit events."""
        try:
            # Hook into trace to capture updates
            trace = state.get("trace")
            if trace:
                trace._execution_streamer = self
            
            # Create streaming callback for AgentMessenger
            async def streaming_callback(message: str):
                """Callback for AgentMessenger to emit stream events."""
                await self.event_queue.put(StreamEvent(
                    event_type="trace_update",
                    message=message  # Preserve newlines from AgentMessenger
                ))
            
            # Execute workflow with streaming callback
            config = {"configurable": {"streaming_callback": streaming_callback}}
            final_state = await workflow.ainvoke(state, config=config)
            
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

    def _test_cancel_workflow_task(self):
        """Helper for tests to cancel the internal workflow task."""
        if self._execution_task:
            self._execution_task.cancel()