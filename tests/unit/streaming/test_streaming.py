"""Core Streaming System Tests - validates ExecutionStreamer functionality."""
import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, Mock

from cogency.streaming.execution import ExecutionStreamer, StreamEvent
from cogency.common.types import AgentState, ExecutionTrace
from cogency.context import Context


class TestExecutionStreamer:
    """Test suite for ExecutionStreamer core functionality."""
    
    @pytest.fixture
    def mock_workflow(self):
        """Mock workflow for testing."""
        workflow = Mock()
        workflow.ainvoke = AsyncMock()
        return workflow
    
    @pytest.fixture
    def test_state(self):
        """Test agent state."""
        trace = ExecutionTrace()
        context = Context(current_input="test query")
        return {
            "query": "test query",
            "trace": trace,
            "context": context
        }
    
    async def test_streaming_executor_lifecycle(self, mock_workflow, test_state):
        """Test complete streaming execution lifecycle."""
        executor = ExecutionStreamer()
        
        # Mock workflow to return final state
        final_state = {"result": "test response"}
        mock_workflow.ainvoke.return_value = final_state
        
        # Collect all events
        events = []
        async for event in executor.astream_execute(mock_workflow, test_state):
            events.append(event)
        
        # Verify lifecycle
        assert len(events) >= 1
        assert events[-1].event_type == "final_state"
        assert events[-1].data["state"] == final_state
        assert executor.final_state == final_state
        assert executor.is_streaming == False
        
        # Verify workflow was called
        mock_workflow.ainvoke.assert_called_once_with(test_state)
    
    async def test_streaming_executor_with_trace_updates(self, mock_workflow, test_state):
        """Test streaming executor captures trace updates."""
        executor = ExecutionStreamer()
        
        # Mock workflow that adds trace entries
        async def mock_workflow_with_traces(state):
            trace = state["trace"]
            trace.add("memorize", "Processing query")
            await asyncio.sleep(0)
            trace.add("select_tools", "Selected tools")
            await asyncio.sleep(0)
            trace.add("reason", "Generated response")
            await asyncio.sleep(0)
            return {"result": "test response"}
        
        mock_workflow.ainvoke.side_effect = mock_workflow_with_traces
        
        # Collect events
        events = []
        async for event in executor.astream_execute(mock_workflow, test_state):
            events.append(event)
        
        # Should have trace_update events + final_state event
        trace_events = [e for e in events if e.event_type == "trace_update"]
        final_events = [e for e in events if e.event_type == "final_state"]
        
        assert len(trace_events) == 3  # One for each trace.add() call
        assert len(final_events) == 1
        
        # Verify trace event content
        assert trace_events[0].node == "memorize"
        assert trace_events[0].message == "Processing query"
        assert trace_events[1].node == "select_tools"
        assert trace_events[2].node == "reason"
    
    async def test_streaming_executor_error_handling(self, mock_workflow, test_state):
        """Test streaming executor handles workflow errors."""
        executor = ExecutionStreamer()
        
        # Mock workflow that raises exception
        mock_workflow.ainvoke.side_effect = RuntimeError("Workflow failed")
        
        # Collect events
        events = []
        with pytest.raises(RuntimeError, match="Workflow failed"):
            async for event in executor.astream_execute(mock_workflow, test_state):
                events.append(event)
        
        # Should have error event
        error_events = [e for e in events if e.event_type == "error"]
        assert len(error_events) == 1
        assert "Workflow failed" in error_events[0].data["error"]
    
    async def test_concurrent_streaming_sessions(self, mock_workflow):
        """Test multiple agents streaming simultaneously."""
        executor1 = ExecutionStreamer()
        executor2 = ExecutionStreamer()
        
        # Create separate states
        trace1 = ExecutionTrace()
        trace2 = ExecutionTrace()
        state1 = {"query": "query1", "trace": trace1, "context": Context(current_input="query1")}
        state2 = {"query": "query2", "trace": trace2, "context": Context(current_input="query2")}
        
        # Mock workflows with different responses
        workflow1 = Mock()
        workflow2 = Mock()
        
        async def mock_workflow1(state):
            trace = state["trace"]
            trace.add("node1", "message1")
            await asyncio.sleep(0.1)  # Simulate work
            return {"result": "response1"}
        
        async def mock_workflow2(state):
            trace = state["trace"]
            trace.add("node2", "message2")
            await asyncio.sleep(0.05)  # Different timing
            return {"result": "response2"}
        
        workflow1.ainvoke.side_effect = mock_workflow1
        workflow2.ainvoke.side_effect = mock_workflow2
        
        # Run concurrent streams
        async def collect_events(executor, workflow, state):
            events = []
            async for event in executor.astream_execute(workflow, state):
                events.append(event)
            return events
        
        # Execute both streams concurrently
        task1 = asyncio.create_task(collect_events(executor1, workflow1, state1))
        task2 = asyncio.create_task(collect_events(executor2, workflow2, state2))
        
        events1, events2 = await asyncio.gather(task1, task2)
        
        # Verify both streams completed independently
        assert len(events1) >= 1
        assert len(events2) >= 1
        
        # Verify final states are correct
        final1 = [e for e in events1 if e.event_type == "final_state"]
        final2 = [e for e in events2 if e.event_type == "final_state"]
        
        assert len(final1) == 1
        assert len(final2) == 1
        assert final1[0].data["state"]["result"] == "response1"
        assert final2[0].data["state"]["result"] == "response2"
        
        # Verify trace updates were isolated
        trace1_events = [e for e in events1 if e.event_type == "trace_update"]
        trace2_events = [e for e in events2 if e.event_type == "trace_update"]
        
        assert len(trace1_events) == 1
        assert len(trace2_events) == 1
        assert trace1_events[0].node == "node1"
        assert trace2_events[0].node == "node2"
    
    async def test_streaming_cancellation(self, mock_workflow, test_state):
        """Test graceful stream cancellation."""
        executor = ExecutionStreamer()

        # Mock workflow that runs indefinitely
        async def long_running_workflow(state):
            await asyncio.Future()  # Runs indefinitely until cancelled
            return {"result": "should not reach here"}

        mock_workflow.ainvoke.side_effect = long_running_workflow

        # Start streaming as a task
        stream_task = asyncio.create_task(self._run_stream_to_completion(executor, mock_workflow, test_state))

        # Prime the generator by awaiting its first element
        # This ensures the workflow task is running before cancellation
        await asyncio.sleep(0.01) # Give a chance for the task to start

        # Cancel the underlying workflow task directly
        executor._test_cancel_workflow_task()

        # Verify cancellation propagates when awaiting the stream task
        with pytest.raises(asyncio.CancelledError):
            await stream_task

        # Verify executor state is clean
        assert executor.is_streaming == False
        assert executor.final_state is None

    async def _run_stream_to_completion(self, executor, workflow, state):
        """Helper to run the stream until completion or cancellation."""
        async for _ in executor.astream_execute(workflow, state):
            pass
    
    async def test_streaming_timeout_handling(self, mock_workflow, test_state):
        """Test streaming handles timeout scenarios correctly."""
        executor = ExecutionStreamer()
        
        # Mock workflow that completes normally
        mock_workflow.ainvoke.return_value = {"result": "test response"}
        
        # Collect events with timeout tracking
        events = []
        start_time = asyncio.get_event_loop().time()
        
        async for event in executor.astream_execute(mock_workflow, test_state):
            events.append(event)
            
        end_time = asyncio.get_event_loop().time()
        
        # Should complete quickly without timeout issues
        assert (end_time - start_time) < 1.0
        assert len(events) >= 1
        assert events[-1].event_type == "final_state"
    
    async def test_emit_trace_update(self):
        """Test direct trace update emission."""
        executor = ExecutionStreamer()
        executor.is_streaming = True
        
        # Emit trace update
        await executor.emit_trace_update("test_node", "test_message", {"key": "value"}, 123.45)
        
        # Should have event in queue
        assert not executor.event_queue.empty()
        
        event = await executor.event_queue.get()
        assert event.event_type == "trace_update"
        assert event.node == "test_node"
        assert event.message == "test_message"
        assert event.data == {"key": "value"}
        assert event.timestamp == 123.45
    
    async def test_emit_trace_update_when_not_streaming(self):
        """Test trace update emission when not streaming."""
        executor = ExecutionStreamer()
        executor.is_streaming = False
        
        # Emit trace update - should be ignored
        await executor.emit_trace_update("test_node", "test_message")
        
        # Queue should be empty
        assert executor.event_queue.empty()
    
    


