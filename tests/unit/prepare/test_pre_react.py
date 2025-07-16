"""Unit tests for pre_react node logic."""
import pytest
from unittest.mock import Mock, AsyncMock

from cogency.prepare.pre_react import pre_react_node
from cogency.prepare.memory import should_extract_memory, save_extracted_memory
from cogency.prepare.tools import create_registry_lite, filter_tools_by_exclusion, prepare_tools_for_react
from cogency.prepare.extract import extract_memory_and_filter_tools
from cogency.common.types import AgentState
from cogency.context import Context
from cogency.utils.tracing import ExecutionTrace


class TestPreReactNode:
    """Test pre_react_node functionality."""

    @pytest.fixture
    def mock_llm(self):
        """Mock LLM."""
        llm = Mock()
        llm.invoke = AsyncMock(return_value='{"memory": "Important sales pattern discovered", "reasoning": "Calculator needed for math, recall for context", "excluded_tools": ["timezone", "weather"]}')
        return llm

    @pytest.fixture
    def mock_memory(self):
        """Mock memory."""
        memory = Mock()
        memory.memorize = AsyncMock(return_value=Mock(id="test-id"))
        return memory

    @pytest.fixture
    def mock_tools(self):
        """Mock tools."""
        tools = []
        for name in ['calculator', 'file_manager', 'timezone', 'weather', 'web_search', 'memorize', 'recall']:
            tool = Mock()
            tool.name = name
            tool.description = f"A {name} tool"
            tool.get_schema = Mock(return_value=f"{name}(param='value')")
            tool.get_usage_examples = Mock(return_value=[f"{name}(example='test')"])
            tools.append(tool)
        return tools

    @pytest.fixture
    def test_state(self):
        """Test state."""
        context = Context(current_input='I discovered an important pattern - sales increase by 20% every Q4', user_id='test')
        return {
            'query': 'I discovered an important pattern - sales increase by 20% every Q4',
            'context': context,
            'trace': ExecutionTrace()
        }

    @pytest.mark.asyncio
    async def test_pre_react_node_with_memory_extraction(self, mock_llm, mock_memory, mock_tools, test_state):
        """Test pre_react_node with memory extraction."""
        result = await pre_react_node(test_state, llm=mock_llm, tools=mock_tools, memory=mock_memory)
        
        # Check that memory was saved
        mock_memory.memorize.assert_called_once()
        
        # Check that tools were filtered
        assert "selected_tools" in result
        selected_names = [t.name for t in result["selected_tools"]]
        
        # Should include calculator and recall, but not memorize
        assert "calculator" in selected_names
        assert "recall" in selected_names
        assert "memorize" not in selected_names

    @pytest.mark.asyncio
    async def test_pre_react_node_simple_case(self, mock_llm, mock_memory):
        """Test pre_react_node with simple case (few tools, no memory extraction)."""
        simple_tools = [Mock(name="calculator"), Mock(name="recall"), Mock(name="memorize")]
        for tool in simple_tools:
            tool.description = f"A {tool.name} tool"
        
        # Use a simple query that doesn't trigger memory extraction
        context = Context(current_input='What is 2+2?', user_id='test')
        simple_state = {
            'query': 'What is 2+2?',
            'context': context,
            'trace': ExecutionTrace()
        }
        
        result = await pre_react_node(simple_state, llm=mock_llm, tools=simple_tools, memory=mock_memory)
        
        # Should not call LLM for simple cases
        mock_llm.invoke.assert_not_called()
        
        # Should still filter out memorize
        selected_names = [t.name for t in result["selected_tools"]]
        assert "memorize" not in selected_names

    def test_should_extract_memory(self):
        """Test memory extraction heuristic."""
        # Should extract
        assert should_extract_memory("I discovered an important pattern")
        assert should_extract_memory("Remember this solution")
        assert should_extract_memory("I found a fix for the bug")
        
        # Should not extract
        assert not should_extract_memory("What is 2+2?")
        assert not should_extract_memory("Hello world")

    @pytest.mark.asyncio
    async def test_save_extracted_memory(self, mock_memory):
        """Test memory saving logic."""
        # Should save non-null/empty memory
        await save_extracted_memory("Important insight", mock_memory, "test-user")
        mock_memory.memorize.assert_called_once_with("Important insight", tags=["insight"], user_id="test-user")
        
        # Should not save null memory
        mock_memory.reset_mock()
        await save_extracted_memory(None, mock_memory, "test-user")
        mock_memory.memorize.assert_not_called()
        
        # Should not save empty memory
        mock_memory.reset_mock()
        await save_extracted_memory("", mock_memory, "test-user")
        mock_memory.memorize.assert_not_called()

    def test_create_registry_lite(self, mock_tools):
        """Test registry lite creation."""
        registry_lite = create_registry_lite(mock_tools)
        
        # Should contain names and descriptions
        assert "calculator: A calculator tool" in registry_lite
        assert "recall: A recall tool" in registry_lite
        assert "memorize: A memorize tool" in registry_lite

    def test_filter_tools_by_exclusion(self, mock_tools):
        """Test tool filtering by exclusion."""
        # Test exclusion filtering
        result = filter_tools_by_exclusion(mock_tools, ["timezone", "weather"])
        selected_names = [t.name for t in result]
        assert "timezone" not in selected_names
        assert "weather" not in selected_names
        assert "calculator" in selected_names
        assert "recall" in selected_names
        assert len(result) == 5  # 7 - 2 excluded
        
        # Test no exclusions (keep all)
        result = filter_tools_by_exclusion(mock_tools, [])
        assert len(result) == 7

    def test_prepare_tools_for_react(self, mock_tools):
        """Test preparing tools for ReAct (remove memorize)."""
        result = prepare_tools_for_react(mock_tools)
        selected_names = [t.name for t in result]
        
        # Should not contain memorize
        assert "memorize" not in selected_names
        
        # Should contain other tools
        assert "calculator" in selected_names
        assert "recall" in selected_names
        assert "file_manager" in selected_names

    @pytest.mark.asyncio
    async def test_extract_memory_and_filter_tools(self, mock_llm):
        """Test LLM extraction function."""
        registry_lite = "- calculator: A calculator tool\n- recall: A recall tool"
        
        result = await extract_memory_and_filter_tools("Test query", registry_lite, mock_llm)
        
        # Should call LLM
        mock_llm.invoke.assert_called_once()
        
        # Should return expected structure
        assert "memory_summary" in result
        assert "reasoning" in result
        assert "excluded_tools" in result
        assert result["memory_summary"] == "Important sales pattern discovered"
        assert result["excluded_tools"] == ["timezone", "weather"]