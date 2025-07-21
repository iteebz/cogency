"""Test the main Agent class and its configuration."""
import pytest
from unittest.mock import AsyncMock, patch

from cogency import Agent
from cogency.llm.mock import MockLLM
from cogency.tools.calculator import Calculator
from cogency.tools.recall import Recall

class TestAgentInitialization:
    """Test the pragmatic setup of the Agent class."""

    def test_agent_defaults(self):
        """Agent should have sane defaults: memory, default tools, etc."""
        agent = Agent("test_agent", llm=MockLLM())

        assert agent.flow is not None
        assert agent.flow.memory is not None, "Memory should be enabled by default"
        
        # Check for default tools + recall
        tool_names = [tool.name for tool in agent.flow.tools]
        assert "recall" in tool_names, "Recall tool should be present when memory is enabled"
        assert "calculator" in tool_names, "Default tools should be loaded"

    def test_agent_memory_disabled(self):
        """Agent with memory=False should not have memory or recall tool."""
        agent = Agent(llm=MockLLM(), memory=False)

        assert agent.flow.memory is None, "Memory should be disabled"
        
        tool_names = [tool.name for tool in agent.flow.tools]
        assert "recall" not in tool_names, "Recall tool should not be present when memory is disabled"

    def test_agent_with_custom_tools(self):
        """Agent should correctly handle custom tool lists."""
        agent = Agent(llm=MockLLM(), tools=[Calculator()], memory=False)

        tool_names = [tool.name for tool in agent.flow.tools]
        assert tool_names == ["calculator"], "Should only have the custom tool"

    def test_agent_with_custom_tools_and_memory(self):
        """Agent should add Recall tool to custom tool list when memory is on."""
        agent = Agent(llm=MockLLM(), tools=[Calculator()], memory=True)

        tool_names = [tool.name for tool in agent.flow.tools]
        assert "calculator" in tool_names
        assert "recall" in tool_names
        assert len(agent.flow.tools) == 2

@pytest.mark.asyncio
async def test_agent_run_calls_flow_execute():
    """Ensure Agent.run() is a clean entrypoint to Flow.execute()."""
    agent = Agent(llm=MockLLM())
    
    # Patch the actual execution engine to keep the test focused and fast.
    # We don't need to test the full flow here, just that the Agent class
    # correctly invokes it.
    with patch('cogency.flow.Flow.execute', new_callable=AsyncMock) as mock_execute:
        mock_execute.return_value = "Final Answer"
        
        result = await agent.run("test query")

        # Verify the agent passed the query to the flow
        mock_execute.assert_called_once()
        call_args = mock_execute.call_args[0]
        assert call_args[0] == "test query"
        
        # Verify the agent returned the flow's result
        assert result == "Final Answer"
