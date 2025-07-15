"""Core business logic tests - ZERO BULLSHIT."""
import pytest
from cogency import Agent


class TestAgent:
    """Test core Agent functionality."""
    
    def test_agent_init(self, mock_llm):
        """Agent initializes with name and LLM."""
        agent = Agent(name="test", llm=mock_llm)
        assert agent.name == "test"
        assert agent.llm is not None
        assert agent.workflow is not None
        assert isinstance(agent.tools, list)

    @pytest.mark.asyncio
    async def test_agent_run(self, mock_llm):
        """Agent can run and return a string response."""
        agent = Agent(name="test", llm=mock_llm, trace=False)
        result = await agent.run("What is 2+2?")
        assert isinstance(result, str)
        assert len(result) > 0