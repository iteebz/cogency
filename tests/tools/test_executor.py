"""Test smart parallel execution with dependency detection."""
import pytest
from unittest.mock import AsyncMock, Mock

from cogency.tools.executor import needs_sequential, run_tools
from cogency.context import Context


class TestSmartParallelDetection:
    """Test dependency risk detection."""
    
    def test_no_dependency_risk_with_independent_tools(self):
        """Independent tools should run in parallel."""
        tool_calls = [
            ("search", {"query": "cats"}),
            ("weather", {"city": "SF"}),
            ("calculate", {"expr": "2+2"})
        ]
        assert needs_sequential(tool_calls) is False
    
    def test_dependency_risk_with_file_and_shell(self):
        """File ops + shell ops should be detected as risky."""
        tool_calls = [
            ("create_file", {"path": "test.py", "content": "print('hello')"}),
            ("run_shell", {"command": "python test.py"})
        ]
        assert needs_sequential(tool_calls) is True
    
    def test_no_dependency_risk_with_file_ops_only(self):
        """Multiple file ops without shell should run parallel."""
        tool_calls = [
            ("create_file", {"path": "a.txt", "content": "file a"}),
            ("create_file", {"path": "b.txt", "content": "file b"})
        ]
        assert needs_sequential(tool_calls) is False
    
    def test_no_dependency_risk_with_shell_ops_only(self):
        """Multiple shell ops without file creation should run parallel."""
        tool_calls = [
            ("run_shell", {"command": "echo hello"}),
            ("run_shell", {"command": "date"})
        ]
        assert needs_sequential(tool_calls) is False


class TestSmartParallelExecution:
    """Test smart parallel execution behavior."""
    
    @pytest.mark.asyncio
    async def test_parallel_execution_for_safe_tools(self):
        """Safe tools should execute in parallel mode."""
        # Mock tools
        search_tool = Mock()
        search_tool.name = "search"
        search_tool.execute = AsyncMock(return_value={"success": True, "result": "search results"})
        
        weather_tool = Mock()
        weather_tool.name = "weather"
        weather_tool.execute = AsyncMock(return_value={"success": True, "result": "sunny"})
        
        tools = [search_tool, weather_tool]
        context = Mock()
        context.add_tool_result = Mock()
        context.add_message = Mock()
        
        tool_calls = [
            ("search", {"query": "cats"}),
            ("weather", {"city": "SF"})
        ]
        
        result = await run_tools(tool_calls, tools, context)
        
        # Should execute in parallel mode
        assert result["execution_mode"] == "parallel"
        assert result["success"] is True
        assert result["successful_count"] == 2
    
    @pytest.mark.asyncio
    async def test_sequential_execution_for_risky_tools(self):
        """Risky tools should execute in sequential mode."""
        # Mock tools
        file_tool = Mock()
        file_tool.name = "create_file"
        file_tool.execute = AsyncMock(return_value={"success": True, "result": "file created"})
        
        shell_tool = Mock()
        shell_tool.name = "run_shell"
        shell_tool.execute = AsyncMock(return_value={"success": True, "result": "command executed"})
        
        tools = [file_tool, shell_tool]
        context = Mock()
        context.add_tool_result = Mock()
        context.add_message = Mock()
        
        tool_calls = [
            ("create_file", {"path": "test.py", "content": "print('hello')"}),
            ("run_shell", {"command": "python test.py"})
        ]
        
        result = await run_tools(tool_calls, tools, context)
        
        # Should execute in sequential mode
        assert result["execution_mode"] == "sequential"
        assert result["success"] is True
        assert result["successful_count"] == 2
        
        # Should log the dependency detection
        context.add_message.assert_any_call("system", "🔒 Dependency detected in tools ['create_file', 'run_shell'] - switching to sequential execution")