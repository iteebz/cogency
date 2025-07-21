"""Tests for enhanced reasoning node."""
import pytest
from unittest.mock import Mock, AsyncMock
from cogency.nodes.reason import reason_node
from cogency.nodes.reasoning import (
    create_action_fingerprint,
    detect_action_loop,
    assess_tool_quality
)
from cogency.state import AgentState


class MockToolCall:
    """Mock tool call for testing."""
    def __init__(self, name, args):
        self.name = name
        self.args = args


class TestActionFingerprinting:
    """Test action fingerprinting for loop detection."""
    
    def test_empty_tool_calls(self):
        """Test fingerprinting with no tool calls."""
        result = create_action_fingerprint([])
        assert result == "no_action"
    
    def test_single_tool_call(self):
        """Test fingerprinting with single tool call."""
        tool_calls = [MockToolCall("search", {"query": "test"})]
        result = create_action_fingerprint(tool_calls)
        assert result.startswith("search:")
        # Just check that the fingerprint contains a hash (numbers)
    
    def test_multiple_tool_calls(self):
        """Test fingerprinting with multiple tool calls."""
        tool_calls = [
            MockToolCall("search", {"query": "test1"}),
            MockToolCall("scrape", {"url": "http://example.com"})
        ]
        result = create_action_fingerprint(tool_calls)
        assert "|" in result
        assert "search:" in result
        assert "scrape:" in result
    
    def test_identical_calls_same_fingerprint(self):
        """Test that identical calls produce same fingerprint."""
        tool_calls1 = [MockToolCall("search", {"query": "test"})]
        tool_calls2 = [MockToolCall("search", {"query": "test"})]
        
        fp1 = create_action_fingerprint(tool_calls1)
        fp2 = create_action_fingerprint(tool_calls2)
        
        assert fp1 == fp2
    
    def test_different_calls_different_fingerprint(self):
        """Test that different calls produce different fingerprints."""
        tool_calls1 = [MockToolCall("search", {"query": "test1"})]
        tool_calls2 = [MockToolCall("search", {"query": "test2"})]
        
        fp1 = create_action_fingerprint(tool_calls1)
        fp2 = create_action_fingerprint(tool_calls2)
        
        assert fp1 != fp2


class TestLoopDetection:
    """Test loop detection logic."""
    
    def test_no_loop_insufficient_history(self):
        """Test no loop detected with insufficient history."""
        cognitive_state = {"action_history": ["action1", "action2"]}
        assert not detect_action_loop(cognitive_state)
    
    def test_no_loop_different_actions(self):
        """Test no loop detected with different actions."""
        cognitive_state = {"action_history": ["action1", "action2", "action3"]}
        assert not detect_action_loop(cognitive_state)
    
    def test_loop_identical_actions(self):
        """Test loop detected with identical repeated actions."""
        cognitive_state = {"action_history": ["action1", "action1", "action1"]}
        assert detect_action_loop(cognitive_state)
    
    def test_loop_alternating_pattern(self):
        """Test loop detected with A-B-A pattern."""
        cognitive_state = {"action_history": ["action1", "action2", "action1"]}
        assert detect_action_loop(cognitive_state)
    
    def test_no_loop_aba_pattern_with_different_middle(self):
        """Test no false positive for A-B-A where A's are different."""
        cognitive_state = {"action_history": ["action1", "action2", "action3"]}
        assert not detect_action_loop(cognitive_state)
    
    def test_empty_action_history(self):
        """Test no loop with empty action history."""
        cognitive_state = {"action_history": []}
        assert not detect_action_loop(cognitive_state)
    
    def test_missing_action_history(self):
        """Test no loop with missing action history key."""
        cognitive_state = {}
        assert not detect_action_loop(cognitive_state)


class TestToolQualityAssessment:
    """Test tool result quality assessment."""
    
    def test_empty_results(self):
        """Test assessment with empty results."""
        execution_results = {}
        assert assess_tool_quality(execution_results) == "unknown"
    
    def test_failed_execution(self):
        """Test assessment with failed execution."""
        execution_results = {"success": False}
        assert assess_tool_quality(execution_results) == "failed"
    
    def test_no_results(self):
        """Test assessment with successful execution but no results."""
        execution_results = {"success": True, "results": []}
        assert assess_tool_quality(execution_results) == "poor"
    
    def test_good_quality(self):
        """Test assessment with good quality results."""
        execution_results = {
            "success": True,
            "results": ["result1", "result2"],
            "successful_count": 4,
            "failed_count": 1
        }
        assert assess_tool_quality(execution_results) == "good"
    
    def test_partial_quality(self):
        """Test assessment with partial quality results."""
        execution_results = {
            "success": True,
            "results": ["result1"],
            "successful_count": 3,
            "failed_count": 2
        }
        assert assess_tool_quality(execution_results) == "partial"
    
    def test_poor_quality(self):
        """Test assessment with poor quality results."""
        execution_results = {
            "success": True,
            "results": ["result1"],
            "successful_count": 1,
            "failed_count": 4
        }
        assert assess_tool_quality(execution_results) == "poor"
    
    def test_unknown_quality_zero_total(self):
        """Test assessment with zero total count."""
        execution_results = {
            "success": True,
            "results": ["result1"],
            "successful_count": 0,
            "failed_count": 0
        }
        assert assess_tool_quality(execution_results) == "unknown"


class TestReasonNode:
    """Test enhanced reason node functionality."""
    
    @pytest.fixture
    def mock_context(self):
        """Create mock context."""
        context = Mock()
        context.messages = []
        context.current_input = "test query"
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
        tool.get_schema = Mock(return_value="test schema")
        tool.get_usage_examples = Mock(return_value=[])
        return [tool]
    
    @pytest.fixture
    def basic_state(self, mock_context):
        """Create basic agent state."""
        from cogency.output import OutputManager
        
        state = AgentState(
            context=mock_context,
            query="test query",
            output=OutputManager()
        )
        return state
    
    @pytest.mark.asyncio
    async def test_cognitive_state_initialization(self, basic_state, mock_llm, mock_tools):
        """Test that cognitive state gets initialized properly."""
        result = await reason_node(basic_state, llm=mock_llm, tools=mock_tools)
        
        assert "cognitive_state" in result
        cognitive_state = result["cognitive_state"]
        assert "strategy_history" in cognitive_state
        assert "failed_attempts" in cognitive_state
        assert "action_history" in cognitive_state
        assert cognitive_state["current_strategy"] == "initial_approach"
    
    @pytest.mark.asyncio
    async def test_iteration_tracking(self, basic_state, mock_llm, mock_tools):
        """Test iteration counter increments."""
        basic_state["current_iteration"] = 2
        
        result = await reason_node(basic_state, llm=mock_llm, tools=mock_tools)
        
        assert result["current_iteration"] == 3
    
    @pytest.mark.asyncio
    async def test_max_iterations_stopping(self, basic_state, mock_llm, mock_tools):
        """Test that reasoning stops at max iterations."""
        basic_state["current_iteration"] = 5
        basic_state["max_iterations"] = 5
        
        result = await reason_node(basic_state, llm=mock_llm, tools=mock_tools)
        
        assert result["stopping_reason"] == "max_iterations_reached"
        assert result["next_node"] == "respond"
    
    @pytest.mark.asyncio
    async def test_loop_detection_stopping(self, basic_state, mock_llm, mock_tools):
        """Test that reasoning stops when loop detected."""
        basic_state["cognitive_state"] = {
            "action_history": ["action1", "action1", "action1"],
            "strategy_history": [],
            "failed_attempts": [],
            "current_strategy": "test",
            "last_tool_quality": "unknown"
        }
        
        result = await reason_node(basic_state, llm=mock_llm, tools=mock_tools)
        
        assert result["stopping_reason"] == "reasoning_loop_detected"
        assert result["next_node"] == "respond"
    
    @pytest.mark.asyncio
    async def test_graceful_degradation_on_llm_error(self, basic_state, mock_llm, mock_tools):
        """Test graceful degradation when LLM fails."""
        mock_llm.run.side_effect = Exception("LLM error")
        
        result = await reason_node(basic_state, llm=mock_llm, tools=mock_tools)
        
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
        
        result = await reason_node(basic_state, llm=mock_llm, tools=mock_tools)
        
        cognitive_state = result["cognitive_state"]
        assert len(cognitive_state["failed_attempts"]) == 1
        assert cognitive_state["failed_attempts"][0]["tool"] == "search"
        assert cognitive_state["failed_attempts"][0]["reason"] == "poor"
    
    @pytest.mark.asyncio
    async def test_memory_limit_enforcement(self, basic_state, mock_llm, mock_tools):
        """Test that memory limits are enforced."""
        # Create state with excessive history
        basic_state["cognitive_state"] = {
            "action_history": [f"action{i}" for i in range(15)],  # Over limit of 10
            "strategy_history": [f"strategy{i}" for i in range(8)],  # Over limit of 5
            "failed_attempts": [],
            "current_strategy": "test",
            "last_tool_quality": "unknown"
        }
        
        # Mock tool calls to trigger history update
        mock_llm.run.return_value = '{"reasoning": "test", "strategy": "new_strategy", "tool_calls": [{"name": "test", "args": {}}]}'
        
        result = await reason_node(basic_state, llm=mock_llm, tools=mock_tools)
        
        cognitive_state = result["cognitive_state"]
        assert len(cognitive_state["action_history"]) <= 10
        assert len(cognitive_state["strategy_history"]) <= 5