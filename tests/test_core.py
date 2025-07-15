"""Core business logic tests - ZERO BULLSHIT."""
import pytest
from cogency import Agent


class TestAgent:
    """Test core Agent functionality."""
    
    @pytest.mark.asyncio
    async def test_agent_basic_run(self, mock_llm):
        """Agent can run and return a string response."""
        agent = Agent(name="test", llm=mock_llm)
        result = await agent.run("What is 2+2?")
        assert isinstance(result, str)
        assert len(result) > 0
    
    @pytest.mark.asyncio
    async def test_agent_streaming(self, mock_llm):
        """Agent can stream character-by-character responses."""
        agent = Agent(name="test", llm=mock_llm) 
        chunks = []
        async for chunk in agent.stream("Hello"):
            chunks.append(chunk)
        
        assert len(chunks) > 0
        assert all(isinstance(chunk, str) for chunk in chunks)
        response = "".join(chunks)
        assert len(response) > 0
    
    def test_agent_initialization(self, mock_llm):
        """Agent initializes with name and LLM."""
        agent = Agent(name="test", llm=mock_llm)
        assert agent.name == "test"
        assert agent.llm is not None
        assert agent.workflow is not None
        assert isinstance(agent.tools, list)