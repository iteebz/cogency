"""Tests for coordination primitives."""
import asyncio
import pytest
from unittest.mock import Mock

from cogency.utils.coordination import StateCoordinator, with_timeout, StreamingTimeoutError
from cogency.context import Context


@pytest.fixture
def mock_state():
    """Mock AgentState for testing."""
    context = Mock()
    context.add_message = Mock()
    return {
        "context": context,
        "execution_trace": None
    }


class TestStateCoordinator:
    """Test StateCoordinator for concurrent state management."""
    
    @pytest.mark.asyncio
    async def test_basic_state_mutation(self, mock_state):
        """Test basic state mutation works."""
        coordinator = StateCoordinator(mock_state)
        
        async with coordinator.mutate_state() as state:
            state["test_key"] = "test_value"
        
        final_state = coordinator.get_state()
        assert final_state["test_key"] == "test_value"
    
    @pytest.mark.asyncio
    async def test_concurrent_access_returns_snapshot(self, mock_state):
        """Test that concurrent access gets read-only snapshot."""
        coordinator = StateCoordinator(mock_state)
        
        # Start first mutation (holds lock)
        async def long_mutation():
            async with coordinator.mutate_state() as state:
                state["first"] = "mutation"
                await asyncio.sleep(0.1)  # Hold lock
                
        # Start concurrent access
        async def concurrent_access():
            await asyncio.sleep(0.05)  # Let first get lock
            async with coordinator.mutate_state() as state:
                # This should get snapshot, changes won't persist
                state["concurrent"] = "change"
                return state
        
        # Run both concurrently
        task1 = asyncio.create_task(long_mutation())
        task2 = asyncio.create_task(concurrent_access())
        
        snapshot, _ = await asyncio.gather(task2, task1)
        
        final_state = coordinator.get_state()
        assert final_state["first"] == "mutation"
        assert "concurrent" not in final_state  # Snapshot changes not persisted
        assert snapshot["concurrent"] == "change"  # But snapshot had the change
    
    @pytest.mark.asyncio
    async def test_mutation_rollback_on_error(self, mock_state):
        """Test that failed mutations don't corrupt state."""
        coordinator = StateCoordinator(mock_state)
        original_state = coordinator.get_state().copy()
        
        with pytest.raises(ValueError):
            async with coordinator.mutate_state() as state:
                state["bad_change"] = "should_rollback"
                raise ValueError("Simulated error")
        
        # State should be unchanged
        final_state = coordinator.get_state()
        assert "bad_change" not in final_state
        assert final_state == original_state
    
    @pytest.mark.asyncio
    async def test_update_context_messages(self, mock_state):
        """Test convenience method for message updates."""
        coordinator = StateCoordinator(mock_state)
        
        await coordinator.update_context_messages("user", "test message")
        
        # Check that the method was called on the final state's context
        final_state = coordinator.get_state()
        final_state["context"].add_message.assert_called_once_with("user", "test message")
    
    @pytest.mark.asyncio
    async def test_update_execution_trace_none(self, mock_state):
        """Test trace update when execution_trace is None."""
        coordinator = StateCoordinator(mock_state)
        
        # Should not raise error when execution_trace is None
        await coordinator.update_execution_trace({"step": "data"})
        
        # No changes to state since execution_trace was None
        assert coordinator.get_state()["execution_trace"] is None


class TestWithTimeout:
    """Test timeout wrapper for operations."""
    
    @pytest.mark.asyncio
    async def test_successful_operation(self):
        """Test that successful operations return normally."""
        async def quick_op():
            await asyncio.sleep(0.01)
            return "success"
        
        result = await with_timeout(quick_op(), 1.0, "test_op")
        assert result == "success"
    
    @pytest.mark.asyncio
    async def test_timeout_error(self):
        """Test that slow operations raise StreamingTimeoutError."""
        async def slow_op():
            await asyncio.sleep(1.0)
            return "too_late"
        
        with pytest.raises(StreamingTimeoutError) as exc_info:
            await with_timeout(slow_op(), 0.01, "slow_operation")
        
        error = exc_info.value
        assert error.operation == "slow_operation"
        assert error.timeout == 0.01
        assert "slow_operation timed out after 0.01s" in str(error)
    
    @pytest.mark.asyncio
    async def test_default_operation_name(self):
        """Test default operation name in timeout error."""
        async def slow_op():
            await asyncio.sleep(1.0)
        
        with pytest.raises(StreamingTimeoutError) as exc_info:
            await with_timeout(slow_op(), 0.01)
        
        assert exc_info.value.operation == "operation"


class TestStreamingTimeoutError:
    """Test StreamingTimeoutError exception."""
    
    def test_error_attributes(self):
        """Test that error preserves operation context."""
        error = StreamingTimeoutError(
            "Test timeout", 
            operation="test_op", 
            timeout=5.0
        )
        
        assert str(error) == "Test timeout"
        assert error.operation == "test_op"
        assert error.timeout == 5.0