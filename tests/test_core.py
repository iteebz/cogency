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
    async def test_agent_stream(self, mock_llm):
        """Agent can stream with traces and return a string response."""
        agent = Agent(name="test", llm=mock_llm, trace=False)
        result = await agent.stream("What is 2+2?")
        assert isinstance(result, str)
        assert len(result) > 0
    
    @pytest.mark.asyncio
    async def test_agent_batch_run(self, mock_llm):
        """Agent can run in batch mode without traces."""
        agent = Agent(name="test", llm=mock_llm, trace=True)
        result = await agent.run("What is 2+2?")
        assert isinstance(result, str)
        assert len(result) > 0
    
    @pytest.mark.asyncio
    async def test_streaming_implementation(self, mock_llm):
        """Test that streaming implementation works end-to-end."""
        agent = Agent(name="test", llm=mock_llm, trace=False)
        
        # Test streaming mode
        result = await agent.stream("Test streaming")
        assert isinstance(result, str)
        assert len(result) > 0
        
        # Test batch mode
        result = await agent.run("Test batch")
        assert isinstance(result, str)
        assert len(result) > 0