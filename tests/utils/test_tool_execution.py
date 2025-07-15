#!/usr/bin/env python3
"""Tests for parallel tool execution, error handling, and result aggregation."""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock
from cogency.utils.tool_execution import execute_single_tool, execute_parallel_tools
from cogency.tools.base import BaseTool
from cogency.context import Context


class MockTool(BaseTool):
    """Mock tool for testing."""
    
    def __init__(self, name: str, should_fail: bool = False, delay: float = 0.0):
        super().__init__(name=name, description=f"Mock tool {name}")
        self.should_fail = should_fail
        self.delay = delay
        self.execution_count = 0
    
    def get_schema(self) -> dict:
        """Return mock schema."""
        return {"type": "object", "properties": {"arg": {"type": "string"}}}
    
    def get_usage_examples(self) -> list:
        """Return mock usage examples."""
        return [f"{self.name}(arg='example')"]
    
    async def run(self, **kwargs):
        """Mock implementation with configurable behavior."""
        self.execution_count += 1
        
        if self.delay > 0:
            await asyncio.sleep(self.delay)
        
        if self.should_fail:
            raise ValueError(f"Mock tool {self.name} failed as configured")
        
        return f"Result from {self.name} with args: {kwargs}"
    
    async def validate_and_run(self, **kwargs):
        """Mock implementation with configurable behavior."""
        return await self.run(**kwargs)


class TestSingleToolExecution:
    """Tests for single tool execution with error handling."""
    
    async def test_successful_tool_execution(self):
        """Test successful single tool execution."""
        tool = MockTool("test_tool")
        tools = [tool]
        
        tool_name, args, result = await execute_single_tool("test_tool", {"arg1": "value1"}, tools)
        
        assert tool_name == "test_tool"
        assert args == {"arg1": "value1"}
        assert result["success"] is True
        assert "Result from test_tool" in result["result"]
        assert result["error"] is None
        assert tool.execution_count == 1
    
    async def test_tool_not_found(self):
        """Test handling of non-existent tool."""
        tools = [MockTool("other_tool")]
        
        tool_name, args, result = await execute_single_tool("missing_tool", {"arg1": "value1"}, tools)
        
        assert tool_name == "missing_tool"
        assert args == {"arg1": "value1"}
        assert result["success"] is False
        assert result["result"] is None
        assert "not found" in result["error"]
        assert result["error_type"] == "tool_not_found"
    
    async def test_tool_execution_error(self):
        """Test handling of tool execution errors."""
        tool = MockTool("failing_tool", should_fail=True)
        tools = [tool]
        
        tool_name, args, result = await execute_single_tool("failing_tool", {"arg1": "value1"}, tools)
        
        assert tool_name == "failing_tool"
        assert args == {"arg1": "value1"}
        assert result["success"] is False
        assert result["result"] is None
        assert "failed as configured" in result["error"]
        assert result["error_type"] == "execution_error"
        assert tool.execution_count == 1


class TestParallelToolExecution:
    """Tests for parallel tool execution with error handling."""
    
    async def test_parallel_execution_all_success(self):
        """Test parallel execution with all tools succeeding."""
        tools = [
            MockTool("tool1", delay=0.1),
            MockTool("tool2", delay=0.1),
            MockTool("tool3", delay=0.1)
        ]
        
        context = Context("test input")
        context.add_tool_result = MagicMock()
        context.add_message = MagicMock()
        
        tool_calls = [
            ("tool1", {"arg": "value1"}),
            ("tool2", {"arg": "value2"}),
            ("tool3", {"arg": "value3"})
        ]
        
        start_time = asyncio.get_event_loop().time()
        result = await execute_parallel_tools(tool_calls, tools, context)
        execution_time = asyncio.get_event_loop().time() - start_time
        
        # Should complete in parallel (faster than sequential)
        assert execution_time < 0.3  # Much faster than 0.3s sequential
        
        assert result["success"] is True
        assert len(result["results"]) == 3
        assert len(result["errors"]) == 0
        assert result["successful_count"] == 3
        assert result["failed_count"] == 0
        assert "3 tools executed successfully" in result["summary"]
        
        # Check that all tools were called
        for tool in tools:
            assert tool.execution_count == 1
    
    async def test_parallel_execution_mixed_results(self):
        """Test parallel execution with some successes and failures."""
        tools = [
            MockTool("success_tool1"),
            MockTool("failing_tool", should_fail=True),
            MockTool("success_tool2")
        ]
        
        context = Context("test input")
        context.add_tool_result = MagicMock()
        context.add_message = MagicMock()
        
        tool_calls = [
            ("success_tool1", {"arg": "value1"}),
            ("failing_tool", {"arg": "value2"}),
            ("success_tool2", {"arg": "value3"})
        ]
        
        result = await execute_parallel_tools(tool_calls, tools, context)
        
        assert result["success"] is False  # Overall failure due to one failure
        assert len(result["results"]) == 2  # Two successes
        assert len(result["errors"]) == 1   # One failure
        assert result["successful_count"] == 2
        assert result["failed_count"] == 1
        assert "2 tools executed successfully; 1 tools failed" in result["summary"]
        
        # Check error details
        error = result["errors"][0]
        assert error["tool_name"] == "failing_tool"
        assert error["error_type"] == "execution_error"
        assert "failed as configured" in error["error"]
    
    async def test_parallel_execution_all_failures(self):
        """Test parallel execution with all tools failing."""
        tools = [
            MockTool("fail1", should_fail=True),
            MockTool("fail2", should_fail=True)
        ]
        
        context = Context("test input")
        context.add_tool_result = MagicMock()
        context.add_message = MagicMock()
        
        tool_calls = [
            ("fail1", {"arg": "value1"}),
            ("fail2", {"arg": "value2"})
        ]
        
        result = await execute_parallel_tools(tool_calls, tools, context)
        
        assert result["success"] is False
        assert len(result["results"]) == 0
        assert len(result["errors"]) == 2
        assert result["successful_count"] == 0
        assert result["failed_count"] == 2
        assert "2 tools failed" in result["summary"]
    
    async def test_parallel_execution_empty_tool_calls(self):
        """Test parallel execution with no tool calls."""
        tools = [MockTool("tool1")]
        context = Context("test input")
        context.add_tool_result = MagicMock()
        context.add_message = MagicMock()
        
        result = await execute_parallel_tools([], tools, context)
        
        assert result["success"] is True
        assert len(result["results"]) == 0
        assert len(result["errors"]) == 0
        assert result["summary"] == "No tools to execute"
    
    async def test_parallel_execution_async_exceptions(self):
        """Test handling of asyncio.gather exceptions."""
        # Create a tool that raises an exception during asyncio.gather
        tool = MockTool("exception_tool")
        original_method = tool.validate_and_run
        
        async def raise_exception(**kwargs):
            raise RuntimeError("Async exception during gather")
        
        tool.validate_and_run = raise_exception
        tools = [tool]
        
        context = Context("test input")
        context.add_tool_result = MagicMock()
        context.add_message = MagicMock()
        
        tool_calls = [("exception_tool", {"arg": "value"})]
        
        result = await execute_parallel_tools(tool_calls, tools, context)
        
        assert result["success"] is False
        assert len(result["results"]) == 0
        assert len(result["errors"]) == 1
        assert result["errors"][0]["error_type"] == "execution_error"
        assert "Async exception during gather" in result["errors"][0]["error"]
    
    async def test_parallel_execution_context_integration(self):
        """Test that parallel execution properly integrates with context."""
        tools = [
            MockTool("tool1"),
            MockTool("tool2")
        ]
        
        context = Context("test input")
        context.add_tool_result = MagicMock()
        context.add_message = MagicMock()
        
        tool_calls = [
            ("tool1", {"arg": "value1"}),
            ("tool2", {"arg": "value2"})
        ]
        
        result = await execute_parallel_tools(tool_calls, tools, context)
        
        # Check that context methods were called
        assert context.add_tool_result.call_count == 2
        assert context.add_message.call_count == 1
        
        # Check the combined message content
        combined_message = context.add_message.call_args[0][1]
        assert "Parallel execution results:" in combined_message
        assert "✅ tool1:" in combined_message
        assert "✅ tool2:" in combined_message
    
    async def test_parallel_execution_performance(self):
        """Test that parallel execution is actually faster than sequential."""
        delay = 0.1
        tools = [
            MockTool("tool1", delay=delay),
            MockTool("tool2", delay=delay),
            MockTool("tool3", delay=delay)
        ]
        
        context = Context("test input")
        context.add_tool_result = MagicMock()
        context.add_message = MagicMock()
        
        tool_calls = [
            ("tool1", {"arg": "value1"}),
            ("tool2", {"arg": "value2"}),
            ("tool3", {"arg": "value3"})
        ]
        
        start_time = asyncio.get_event_loop().time()
        result = await execute_parallel_tools(tool_calls, tools, context)
        execution_time = asyncio.get_event_loop().time() - start_time
        
        # Should be much faster than sequential (3 * delay)
        assert execution_time < (delay * 2)  # Should be closer to delay, not 3*delay
        assert result["success"] is True
        assert len(result["results"]) == 3


async def run_parallel_tests():
    """Run all parallel tool execution tests."""
    print("🔄 Testing parallel tool execution...")
    
    # Single tool tests
    single_tests = TestSingleToolExecution()
    await single_tests.test_successful_tool_execution()
    print("✅ Single tool execution success")
    
    await single_tests.test_tool_not_found()
    print("✅ Single tool not found handling")
    
    await single_tests.test_tool_execution_error()
    print("✅ Single tool execution error handling")
    
    # Parallel tool tests
    parallel_tests = TestParallelToolExecution()
    await parallel_tests.test_parallel_execution_all_success()
    print("✅ Parallel execution all success")
    
    await parallel_tests.test_parallel_execution_mixed_results()
    print("✅ Parallel execution mixed results")
    
    await parallel_tests.test_parallel_execution_all_failures()
    print("✅ Parallel execution all failures")
    
    await parallel_tests.test_parallel_execution_empty_tool_calls()
    print("✅ Parallel execution empty calls")
    
    await parallel_tests.test_parallel_execution_async_exceptions()
    print("✅ Parallel execution async exceptions")
    
    await parallel_tests.test_parallel_execution_context_integration()
    print("✅ Parallel execution context integration")
    
    await parallel_tests.test_parallel_execution_performance()
    print("✅ Parallel execution performance")
    
    print("\n🎉 All parallel tool execution tests passed!")


if __name__ == "__main__":
    asyncio.run(run_parallel_tests())