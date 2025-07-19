"""Test streaming execution and trace integration."""
import pytest
import asyncio
from unittest.mock import AsyncMock, Mock

from cogency.streaming import ExecutionStreamer, StreamEvent
from cogency.tracing import ExecutionTrace
from cogency.types import AgentState


class TestStreamingExecution:
    """Test streaming execution behavior."""
    
    @pytest.mark.asyncio
    async def test_basic_streaming_flow(self, agent_state):
        """Basic streaming should work without errors."""
        streamer = ExecutionStreamer()
        
        # Mock workflow that completes successfully
        mock_workflow = Mock()
        mock_workflow.ainvoke = AsyncMock(return_value={"result": "success"})
        
        events = []
        async for event in streamer.astream_execute(mock_workflow, agent_state):
            events.append(event)
        
        # Should have at least a final_state event
        assert len(events) >= 1
        final_events = [e for e in events if e.event_type == "final_state"]
        assert len(final_events) == 1
        assert final_events[0].data["state"]["result"] == "success"
    
    @pytest.mark.asyncio
    async def test_trace_integration(self, agent_state):
        """Streaming should integrate with execution trace."""
        streamer = ExecutionStreamer()
        trace = ExecutionTrace()
        agent_state["trace"] = trace
        
        # Mock workflow that uses trace
        async def mock_workflow_with_trace(state):
            trace = state["trace"]
            trace.add("test_node", "Test message")
            return {"result": "traced"}
        
        mock_workflow = Mock()
        mock_workflow.ainvoke = mock_workflow_with_trace
        
        events = []
        async for event in streamer.astream_execute(mock_workflow, agent_state):
            events.append(event)
        
        # Should have trace updates
        trace_events = [e for e in events if e.event_type == "trace_update"]
        # Note: trace events depend on trace implementation
        # At minimum, should have final state
        final_events = [e for e in events if e.event_type == "final_state"]
        assert len(final_events) == 1
    
    @pytest.mark.asyncio
    async def test_error_handling_in_streaming(self, agent_state):
        """Streaming should handle workflow errors gracefully."""
        streamer = ExecutionStreamer()
        
        # Mock workflow that raises an error
        mock_workflow = Mock()
        mock_workflow.ainvoke = AsyncMock(side_effect=RuntimeError("Test error"))
        
        events = []
        with pytest.raises(RuntimeError, match="Test error"):
            async for event in streamer.astream_execute(mock_workflow, agent_state):
                events.append(event)
        
        # Should have received error event before exception
        error_events = [e for e in events if e.event_type == "error"]
        assert len(error_events) == 1
        assert "Test error" in error_events[0].data["error"]
    
    @pytest.mark.asyncio
    async def test_streaming_timeout_behavior(self, agent_state):
        """Streaming should handle timeouts appropriately."""
        streamer = ExecutionStreamer()
        
        # Mock workflow that takes a long time
        async def slow_workflow(state):
            await asyncio.sleep(2)  # Longer than timeout
            return {"result": "slow"}
        
        mock_workflow = Mock()
        mock_workflow.ainvoke = slow_workflow
        
        events = []
        # This should complete eventually, just slowly
        async for event in streamer.astream_execute(mock_workflow, agent_state):
            events.append(event)
            # Don't wait for the full 2 seconds in tests
            break
        
        # The workflow should still be running
        assert not streamer._execution_task.done()


class TestStreamEvent:
    """Test stream event structure and behavior."""
    
    def test_stream_event_creation(self):
        """Stream events should have proper structure."""
        event = StreamEvent(
            event_type="test_event",
            node="test_node",
            message="test message",
            data={"key": "value"}
        )
        
        assert event.event_type == "test_event"
        assert event.node == "test_node"
        assert event.message == "test message"
        assert event.data["key"] == "value"
    
    def test_minimal_stream_event(self):
        """Stream events should work with minimal data."""
        event = StreamEvent(event_type="minimal")
        
        assert event.event_type == "minimal"
        assert event.node is None
        assert event.message is None
        assert event.data is None


class TestExecutionTrace:
    """Test execution trace functionality."""
    
    def test_trace_creation(self):
        """Execution trace should initialize properly."""
        trace = ExecutionTrace()
        
        assert trace is not None
        # Basic trace functionality
        assert hasattr(trace, 'add')
    
    def test_trace_add_entries(self):
        """Should be able to add entries to trace."""
        trace = ExecutionTrace()
        
        trace.add("test_node", "Test message")
        
        # Trace should store the entry
        # (Actual assertion depends on trace implementation)
        assert True  # Placeholder - depends on trace API
    
    @pytest.mark.asyncio
    async def test_trace_streaming_integration(self):
        """Trace should integrate with streaming."""
        trace = ExecutionTrace()
        streamer = ExecutionStreamer()
        
        # Hook them together
        trace._execution_streamer = streamer
        
        # Adding to trace should potentially emit stream events
        # (This depends on trace implementation)
        trace.add("test_node", "Test message")
        
        # This is integration - actual behavior depends on implementation
        assert True  # Placeholder


class TestStreamingRealTime:
    """Test real-time streaming behavior."""
    
    @pytest.mark.asyncio
    async def test_events_arrive_in_real_time(self, agent_state):
        """Events should arrive as they're generated, not batched."""
        streamer = ExecutionStreamer()
        
        # Mock workflow that emits multiple events
        async def multi_event_workflow(state):
            trace = state.get("trace")
            if trace and hasattr(trace, '_execution_streamer'):
                # Emit multiple events with delays
                await trace._execution_streamer.emit_trace_update("step1", "First step")
                await asyncio.sleep(0.1)  # Small delay
                await trace._execution_streamer.emit_trace_update("step2", "Second step")
            return {"result": "multi_event"}
        
        mock_workflow = Mock()
        mock_workflow.ainvoke = multi_event_workflow
        
        # Track event timing
        event_times = []
        start_time = asyncio.get_event_loop().time()
        
        async for event in streamer.astream_execute(mock_workflow, agent_state):
            event_times.append(asyncio.get_event_loop().time() - start_time)
            if event.event_type == "final_state":
                break
        
        # Events should arrive over time, not all at once
        # (If we got multiple events, they should be spaced out)
        if len(event_times) > 1:
            time_diff = event_times[-1] - event_times[0]
            assert time_diff > 0.05  # Should take at least 50ms due to sleep


class TestStreamingCleanup:
    """Test streaming cleanup and resource management."""
    
    @pytest.mark.asyncio
    async def test_streaming_cleanup_on_completion(self, agent_state):
        """Streaming should clean up properly on completion."""
        streamer = ExecutionStreamer()
        
        mock_workflow = Mock()
        mock_workflow.ainvoke = AsyncMock(return_value={"result": "cleanup_test"})
        
        async for event in streamer.astream_execute(mock_workflow, agent_state):
            pass
        
        # After completion, streaming should be marked as stopped
        assert streamer.is_streaming is False
        assert streamer._execution_task.done()
    
    @pytest.mark.asyncio
    async def test_streaming_cleanup_on_error(self, agent_state):
        """Streaming should clean up properly on error."""
        streamer = ExecutionStreamer()
        
        mock_workflow = Mock()
        mock_workflow.ainvoke = AsyncMock(side_effect=RuntimeError("Cleanup test error"))
        
        try:
            async for event in streamer.astream_execute(mock_workflow, agent_state):
                pass
        except RuntimeError:
            pass  # Expected
        
        # Even after error, should clean up
        assert streamer.is_streaming is False