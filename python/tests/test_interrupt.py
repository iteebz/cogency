"""Tests for the interrupt functionality."""

import asyncio
import pytest

from cogency.utils.interrupt import interruptable


class TestInterruptable:
    """Test suite for interruptable decorator."""

    @pytest.mark.asyncio
    async def test_interruptable_decorator_basic(self):
        """Test that interruptable decorator works on basic async functions."""
        
        @interruptable
        async def simple_function():
            await asyncio.sleep(0.01)
            return "completed"
        
        result = await simple_function()
        assert result == "completed"

    @pytest.mark.asyncio
    async def test_interruptable_with_cancellation(self):
        """Test that interruptable functions can be cancelled."""
        
        @interruptable
        async def long_running_function():
            await asyncio.sleep(1.0)  # Long operation
            return "should not complete"
        
        task = asyncio.create_task(long_running_function())
        await asyncio.sleep(0.01)  # Let it start
        task.cancel()
        
        with pytest.raises(asyncio.CancelledError):
            await task

    @pytest.mark.asyncio
    async def test_interruptable_preserves_function_signature(self):
        """Test that interruptable preserves function signature and arguments."""
        
        @interruptable
        async def function_with_args(a, b, c=None):
            return f"a={a}, b={b}, c={c}"
        
        result = await function_with_args("test", 42, c="optional")
        assert result == "a=test, b=42, c=optional"

    @pytest.mark.asyncio 
    async def test_interruptable_preserves_exceptions(self):
        """Test that interruptable preserves exceptions from wrapped functions."""
        
        @interruptable
        async def failing_function():
            raise ValueError("Test error")
        
        with pytest.raises(ValueError, match="Test error"):
            await failing_function()