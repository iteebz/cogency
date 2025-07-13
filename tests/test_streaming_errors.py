"""Test cases for streaming error handling in Cogency."""
import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock
from typing import AsyncGenerator, Dict, Any

from cogency.utils.recovery import safe_stream, safe_tool_execution, safe_memory_operation, safe_llm_call
from cogency.utils.coordination import StateCoordinator
from cogency.utils.errors import StreamingToolError, StreamingMemoryError, StreamingLLMError
from cogency.types import AgentState
from cogency.context import Context


@pytest.fixture
def state_coordinator():
    """Create a StateCoordinator for testing."""
    initial_state: AgentState = {
        "context": Context(goal="test", max_iterations=5),
        "execution_trace": None
    }
    return StateCoordinator(initial_state)


class TestSafeStream:
    """Test cases for safe_stream function."""
    
    async def test_successful_streaming(self, state_coordinator):
        """Test normal streaming operation without errors."""
        async def mock_operation():
            yield {"type": "content", "content": "hello"}
            yield {"type": "content", "content": " world"}
        
        results = []
        async for delta in safe_stream(mock_operation, state_coordinator, "test_op"):
            results.append(delta)
        
        assert len(results) == 2
        assert results[0]["content"] == "hello"
        assert results[1]["content"] == " world"
    
    async def test_timeout_handling(self, state_coordinator):
        """Test timeout with proper error yielding."""
        async def slow_operation():
            await asyncio.sleep(2.0)  # Will timeout
            yield {"type": "content", "content": "too slow"}
        
        results = []
        async for delta in safe_stream(slow_operation, state_coordinator, "slow_op", timeout_seconds=0.1):
            results.append(delta)
        
        assert len(results) == 1
        error_delta = results[0]
        assert error_delta["type"] == "error"
        assert "timed out" in error_delta["content"]
        assert error_delta["data"]["error_type"] == "timeout"
        assert "state" in error_delta
    
    async def test_corrupted_delta_validation(self, state_coordinator):
        """Test detection of corrupted stream deltas."""
        async def corrupted_operation():
            yield {"type": "content", "content": "good"}
            yield {"invalid": "structure"}  # Missing type field
            yield {"type": "content", "content": "never reached"}
        
        results = []
        async for delta in safe_stream(corrupted_operation, state_coordinator, "corrupt_op"):
            results.append(delta)
        
        assert len(results) == 2
        assert results[0]["content"] == "good"
        assert results[1]["type"] == "error"
        assert "Corrupted stream delta" in results[1]["content"]
    
    async def test_invalid_llm_content(self, state_coordinator):
        """Test validation of LLM response content."""
        async def invalid_llm_operation():
            yield {"type": "content", "content": "good content"}
            yield {"type": "content", "content": ""}  # Empty content
            yield {"type": "content", "content": "never reached"}
        
        results = []
        async for delta in safe_stream(invalid_llm_operation, state_coordinator, "llm_op"):
            results.append(delta)
        
        assert len(results) == 2
        assert results[0]["content"] == "good content"
        assert results[1]["type"] == "error"
        assert "Invalid LLM response content" in results[1]["content"]
    
    async def test_cancellation_handling(self, state_coordinator):
        """Test proper cancellation of streaming operations."""
        async def cancellable_operation():
            for i in range(10):
                yield {"type": "content", "content": f"chunk {i}"}
                await asyncio.sleep(0.1)
        
        results = []
        task = asyncio.create_task(self._collect_with_cancel(
            safe_stream(cancellable_operation, state_coordinator, "cancel_op"), 
            results
        ))
        
        # Let it process a few deltas then cancel
        await asyncio.sleep(0.15)
        task.cancel()
        
        try:
            await task
        except asyncio.CancelledError:
            pass
        
        # Should have some results but not all 10
        assert len(results) > 0
        assert len(results) < 10
    
    async def _collect_with_cancel(self, stream, results):
        """Helper to collect stream results."""
        async for delta in stream:
            results.append(delta)


class TestSafeToolExecution:
    """Test cases for safe tool execution."""
    
    async def test_successful_tool_execution(self, state_coordinator):
        """Test normal tool execution."""
        async def mock_tool(arg1, arg2):
            return {"result": f"{arg1} + {arg2}"}
        
        result = await safe_tool_execution(
            mock_tool, "test_tool", {"arg1": "hello", "arg2": "world"}, 
            state_coordinator
        )
        
        assert result["result"] == "hello + world"
    
    async def test_tool_timeout(self, state_coordinator):
        """Test tool execution timeout."""
        async def slow_tool():
            await asyncio.sleep(1.0)
            return {"result": "too slow"}
        
        with pytest.raises(StreamingToolError) as exc_info:
            await safe_tool_execution(
                slow_tool, "slow_tool", {}, state_coordinator, timeout_seconds=0.1
            )
        
        error = exc_info.value
        assert "timed out" in error.message
        assert error.tool_name == "slow_tool"
        assert error.agent_state_snapshot is not None
    
    async def test_tool_exception(self, state_coordinator):
        """Test tool execution with exception."""
        async def failing_tool():
            raise ValueError("Tool failed")
        
        with pytest.raises(StreamingToolError) as exc_info:
            await safe_tool_execution(
                failing_tool, "fail_tool", {}, state_coordinator
            )
        
        error = exc_info.value
        assert "execution failed" in error.message
        assert "ValueError" in error.message
        assert error.tool_name == "fail_tool"


class TestSafeMemoryOperation:
    """Test cases for safe memory operations."""
    
    async def test_successful_memory_operation(self, state_coordinator):
        """Test normal memory operation."""
        async def mock_memory_op():
            return {"artifacts": ["memory1", "memory2"]}
        
        result = await safe_memory_operation(
            mock_memory_op, "recall", state_coordinator, content="test query"
        )
        
        assert result["artifacts"] == ["memory1", "memory2"]
    
    async def test_memory_timeout(self, state_coordinator):
        """Test memory operation timeout."""
        async def slow_memory_op():
            await asyncio.sleep(1.0)
            return {"result": "too slow"}
        
        with pytest.raises(StreamingMemoryError) as exc_info:
            await safe_memory_operation(
                slow_memory_op, "slow_recall", state_coordinator, 
                timeout_seconds=0.1, content="test"
            )
        
        error = exc_info.value
        assert "timed out" in error.message
        assert error.operation == "slow_recall"
        assert error.content == "test"


class TestSafeLLMCall:
    """Test cases for safe LLM operations."""
    
    async def test_successful_llm_call(self, state_coordinator):
        """Test normal LLM operation."""
        async def mock_llm_call():
            return "Generated response"
        
        result = await safe_llm_call(
            mock_llm_call, "generate", state_coordinator, prompt="test prompt"
        )
        
        assert result == "Generated response"
    
    async def test_llm_timeout(self, state_coordinator):
        """Test LLM operation timeout."""
        async def slow_llm_call():
            await asyncio.sleep(1.0)
            return "too slow"
        
        with pytest.raises(StreamingLLMError) as exc_info:
            await safe_llm_call(
                slow_llm_call, "slow_generate", state_coordinator, 
                timeout_seconds=0.1, prompt="test"
            )
        
        error = exc_info.value
        assert "timed out" in error.message
        assert error.operation == "slow_generate"
        assert error.prompt == "test"


class TestDeltaValidation:
    """Test delta validation functions."""
    
    def test_valid_delta_structures(self):
        """Test validation of various valid delta structures."""
        from cogency.utils.recovery import _is_valid_delta
        
        valid_deltas = [
            {"type": "content", "content": "hello"},
            {"type": "reasoning", "reasoning": "thinking..."},
            {"type": "tool_call", "tool": "search", "args": {"q": "test"}},
            {"type": "tool_result", "result": {"data": "found"}},
            {"type": "error", "content": "failed", "data": {"code": 500}},
            {"type": "memory", "operation": "recall"},
            {"type": "custom", "data": "anything"}  # Unknown types allowed
        ]
        
        for delta in valid_deltas:
            assert _is_valid_delta(delta), f"Delta should be valid: {delta}"
    
    def test_invalid_delta_structures(self):
        """Test validation catches invalid delta structures."""
        from cogency.utils.recovery import _is_valid_delta
        
        invalid_deltas = [
            "not a dict",
            {},  # Missing type
            {"type": "content"},  # Missing content field
            {"type": "tool_call", "tool": "search"},  # Missing args
            {"type": "error", "content": "failed"},  # Missing data
        ]
        
        for delta in invalid_deltas:
            assert not _is_valid_delta(delta), f"Delta should be invalid: {delta}"
    
    def test_llm_content_validation(self):
        """Test LLM content validation."""
        from cogency.utils.recovery import _is_valid_llm_content
        
        # Valid content
        valid_content = [
            "Hello world",
            "Multi\nline\ncontent",
            "Special chars: !@#$%^&*()",
            "Unicode: 你好世界",
            "ab"  # Minimum length
        ]
        
        for content in valid_content:
            assert _is_valid_llm_content(content), f"Content should be valid: {repr(content)}"
        
        # Invalid content
        invalid_content = [
            "",  # Empty
            "   ",  # Whitespace only
            "a",  # Too short
            123,  # Not string
            "text\x00null",  # Null bytes
            "text\ufffdcorrupt",  # Unicode replacement char
        ]
        
        for content in invalid_content:
            assert not _is_valid_llm_content(content), f"Content should be invalid: {repr(content)}"


if __name__ == "__main__":
    pytest.main([__file__])