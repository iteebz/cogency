"""Tests for enhanced reasoning node integration."""
import pytest
from unittest.mock import Mock, AsyncMock
from cogency.nodes.reason import reason
from cogency.state import State


class MockToolCall:
    """Mock tool call for testing."""
    def __init__(self, name, args):
        self.name = name
        self.args = args


class TestReasonNode:
    """Test enhanced reason node functionality."""
    
    @pytest.fixture
    def mock_context(self):
        """Create mock context."""
        context = Mock()
        context.messages = []
        context.query = "test query"
        context.add_message = Mock()
        return context
    
    @pytest.fixture
    def mock_llm(self):
        """Create mock LLM."""
        llm = AsyncMock()
        llm.run = AsyncMock(return_value='{"reasoning": "test reasoning", "strategy": "test_strategy"}')
        return llm
    
    @pytest.fixture
    def mock_tools(self):
        """Create mock tools."""
        tool = Mock()
        tool.name = "test_tool"
        tool.schema = Mock(return_value="test schema")
        tool.examples = Mock(return_value=[])
        return [tool]
    
    @pytest.fixture
    def basic_state(self, mock_context):
        """Create basic agent state."""
        from cogency.output import Output
        
        state = State(
            context=mock_context,
            query="test query",
            output=Output()
        )
        return state
    
    @pytest.mark.asyncio
    async def test_cognition_initialization(self, basic_state, mock_llm, mock_tools):
        """Test that cognition gets initialized properly."""
        result = await reason(basic_state, llm=mock_llm, tools=mock_tools)
        
        assert "cognition" in result
        cognition = result["cognition"]
        assert "strategy_history" in cognition
        assert "failed_attempts" in cognition
        assert "action_history" in cognition
        assert cognition["current_strategy"] == "initial_approach"
    
    @pytest.mark.asyncio
    async def test_iteration_tracking(self, basic_state, mock_llm, mock_tools):
        """Test iteration counter increments."""
        basic_state["current_iteration"] = 2
        
        result = await reason(basic_state, llm=mock_llm, tools=mock_tools)
        
        assert result["current_iteration"] == 3
    
    @pytest.mark.asyncio
    async def test_max_iterations_stopping(self, basic_state, mock_llm, mock_tools):
        """Test that reasoning stops at max iterations."""
        basic_state["current_iteration"] = 5
        basic_state["max_iterations"] = 5
        
        result = await reason(basic_state, llm=mock_llm, tools=mock_tools)
        
        assert result["stopping_reason"] == "max_iterations_reached"
        assert result["next_node"] == "respond"
    
    @pytest.mark.asyncio
    async def test_loop_detection_stopping(self, basic_state, mock_llm, mock_tools):
        """Test that reasoning stops when loop detected."""
        basic_state["cognition"] = {
            "action_history": ["action1", "action1", "action1"],
            "strategy_history": [],
            "failed_attempts": [],
            "current_strategy": "test",
            "last_tool_quality": "unknown"
        }
        
        result = await reason(basic_state, llm=mock_llm, tools=mock_tools)
        
        assert result["stopping_reason"] == "reasoning_loop_detected"
        assert result["next_node"] == "respond"
    
    @pytest.mark.asyncio
    async def test_graceful_degradation_on_llm_error(self, basic_state, mock_llm, mock_tools):
        """Test graceful degradation when LLM fails."""
        mock_llm.run.side_effect = Exception("LLM error")
        
        result = await reason(basic_state, llm=mock_llm, tools=mock_tools)
        
        assert result["can_answer_directly"] is True
        assert result["tool_calls"] is None
        assert "issue" in result["reasoning_response"]
    
    @pytest.mark.asyncio
    async def test_failed_attempts_tracking(self, basic_state, mock_llm, mock_tools):
        """Test that failed attempts are tracked properly."""
        # Set up previous execution results indicating failure
        basic_state["execution_results"] = {
            "success": True,
            "results": [],
            "successful_count": 0,
            "failed_count": 1
        }
        # Create a dict-like object that has name and args attributes
        class DictLikeTool:
            def __init__(self, name, args):
                self.name = name
                self.args = args
                
            def get(self, key, default=None):
                if key == "function":
                    return {"name": self.name}
                return default
                
        basic_state["prev_tool_calls"] = [DictLikeTool("search", {"query": "test"})]
        
        result = await reason(basic_state, llm=mock_llm, tools=mock_tools)
        
        cognition = result["cognition"]
        assert len(cognition["failed_attempts"]) == 1
        assert cognition["failed_attempts"][0]["tool"] == "search"
        assert cognition["failed_attempts"][0]["reason"] == "poor"
    
    @pytest.mark.asyncio
    async def test_memory_limit_enforcement(self, basic_state, mock_llm, mock_tools):
        """Test that memory limits are enforced."""
        # Create state with excessive history
        basic_state["cognition"] = {
            "action_history": [f"action{i}" for i in range(15)],  # Over limit of 10
            "strategy_history": [f"strategy{i}" for i in range(8)],  # Over limit of 5
            "failed_attempts": [],
            "current_strategy": "test",
            "last_tool_quality": "unknown"
        }
        
        # Mock tool calls to trigger history update
        mock_llm.run.return_value = '{"reasoning": "test", "strategy": "new_strategy", "tool_calls": [{"name": "test", "args": {}}]}'
        
        result = await reason(basic_state, llm=mock_llm, tools=mock_tools)
        
        cognition = result["cognition"]
        assert len(cognition["action_history"]) <= 10
        assert len(cognition["strategy_history"]) <= 5