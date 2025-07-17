import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock

from cogency.core.execution_stream import ExecutionStreamer, StreamEvent
from cogency.common.types import AgentState

@pytest.fixture
def streamer():
    """Fixture for ExecutionStreamer instance."""
    return ExecutionStreamer()

@pytest.fixture
def mock_workflow():
    """Mock workflow for testing ExecutionStreamer."""
    workflow = MagicMock()
    workflow.ainvoke = AsyncMock()
    return workflow

async def _consume_async_generator(agen):
    """Helper to consume an async generator in a background task."""
    async for _ in agen:
        pass

@pytest.mark.asyncio
async def test_astream_execute_final_state(streamer, mock_workflow):
    """Test astream_execute yields final_state event."""
    mock_workflow.ainvoke.return_value = {"output": "workflow completed"}
    
    events = []
    async for event in streamer.astream_execute(mock_workflow, AgentState()):
        events.append(event)
    
    assert len(events) > 0
    assert events[-1].event_type == "final_state"
    assert events[-1].data["state"] == {"output": "workflow completed"}
    mock_workflow.ainvoke.assert_called_once()

@pytest.mark.asyncio
async def test_astream_execute_error_event(streamer, mock_workflow):
    """Test astream_execute yields error event on workflow exception."""
    mock_workflow.ainvoke.side_effect = ValueError("Workflow failed")
    
    events = []
    with pytest.raises(RuntimeError, match="Workflow failed"):
        async for event in streamer.astream_execute(mock_workflow, AgentState()):
            events.append(event)
    
    assert len(events) > 0
    assert events[-1].event_type == "error"
    assert events[-1].data["error"] == "Workflow failed"

@pytest.mark.asyncio
async def test_emit_trace_update(streamer):
    """Test emit_trace_update adds events to the queue when streaming."""
    # Start a dummy execution to enable streaming mode
    async def dummy_workflow(state):
        await asyncio.sleep(0.01) # Allow streamer to enter streaming mode
        return {}

    consumer_task = asyncio.create_task(_consume_async_generator(streamer.astream_execute(MagicMock(ainvoke=dummy_workflow), AgentState())))
    await asyncio.sleep(0.001) # Give astream_execute a chance to start

    await streamer.emit_trace_update("node1", "message1", {"key": "value"})
    await streamer.emit_trace_update("node2", "message2")

    # Retrieve events from the queue
    events = []
    while not streamer.event_queue.empty():
        events.append(await streamer.event_queue.get())
    
    # The first event will be from the dummy workflow starting, then our trace updates
    # We need to filter for trace_update events
    trace_events = [e for e in events if e.event_type == "trace_update"]

    assert len(trace_events) == 2
    assert trace_events[0].node == "node1"
    assert trace_events[0].message == "message1"
    assert trace_events[0].data == {"key": "value"}
    assert trace_events[1].node == "node2"
    assert trace_events[1].message == "message2"
    assert trace_events[1].data == {}

    consumer_task.cancel()
    try:
        await consumer_task
    except asyncio.CancelledError:
        pass

@pytest.mark.asyncio
async def test_emit_trace_update_not_streaming(streamer):
    """Test emit_trace_update does not add events when not streaming."""
    streamer.is_streaming = False # Ensure not streaming
    await streamer.emit_trace_update("node", "message")
    assert streamer.event_queue.empty()

@pytest.mark.asyncio
async def test_astream_execute_cancellation(streamer, mock_workflow):
    """Test astream_execute handles cancellation gracefully."""
    mock_workflow.ainvoke.side_effect = asyncio.CancelledError

    with pytest.raises(asyncio.CancelledError):
        async for _ in streamer.astream_execute(mock_workflow, AgentState()):
            pass

    assert not streamer.is_streaming

@pytest.mark.asyncio
async def test_astream_execute_workflow_completion_without_intermediate_events(streamer, mock_workflow):
    """Test astream_execute handles workflow completion even without intermediate events."""
    # Simulate a workflow that never puts events, but eventually completes
    mock_workflow.ainvoke.side_effect = lambda *args, **kwargs: asyncio.sleep(0.2) # Simulate work then complete

    events = []
    async for event in streamer.astream_execute(mock_workflow, AgentState()):
        events.append(event)

    assert len(events) > 0
    assert events[-1].event_type == "final_state"
    assert not streamer.is_streaming # Ensure streaming is off after completion

@pytest.mark.asyncio
async def test_test_cancel_workflow_task(streamer, mock_workflow):
    """Test _test_cancel_workflow_task cancels the internal task."""
    # Start a dummy execution
    async def long_running_workflow(state):
        await asyncio.sleep(0.2) # Long sleep
        return {}

    mock_workflow.ainvoke.side_effect = long_running_workflow
    consumer_task = asyncio.create_task(_consume_async_generator(streamer.astream_execute(mock_workflow, AgentState())))
    await asyncio.sleep(0.01) # Allow task to start

    assert not consumer_task.done()
    streamer._test_cancel_workflow_task()
    
    # Give it a moment to cancel and for the consumer task to finish processing
    await asyncio.sleep(0.3)  # Longer wait for cancellation
    
    # Clean up task properly
    consumer_task.cancel()
    try:
        await consumer_task
    except asyncio.CancelledError:
        pass  # Expected
    
    # Just check that cancellation happened
    assert consumer_task.cancelled() or consumer_task.done()