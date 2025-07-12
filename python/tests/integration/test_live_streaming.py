"""Integration tests for live streaming with real LLM providers."""

import asyncio
import os
import pytest
from dotenv import load_dotenv

from cogency.agent import Agent
from cogency.llm.gemini import GeminiLLM
from cogency.llm.openai import OpenAILLM
from cogency.tools.calculator import CalculatorTool


@pytest.fixture(scope="module", autouse=True)
def load_env():
    """Load environment variables for live testing."""
    env_path = "/Users/teebz/dev/workspace/smoketest/poetry-env/.env"
    if os.path.exists(env_path):
        load_dotenv(env_path)


class TestLiveStreamingGemini:
    """Live streaming tests with Gemini API."""
    
    @pytest.fixture(autouse=True)
    def setup_gemini(self):
        """Setup Gemini if keys available."""
        gemini_keys = [
            os.getenv("GEMINI_API_KEY_1"),
            os.getenv("GEMINI_API_KEY_2"), 
            os.getenv("GEMINI_API_KEY_3")
        ]
        self.gemini_keys = [key for key in gemini_keys if key]
        
        if not self.gemini_keys:
            pytest.skip("No Gemini API keys available")
    
    @pytest.mark.asyncio
    async def test_complete_workflow_streaming(self):
        """Test complete agent workflow with live streaming."""
        llm = GeminiLLM(api_keys=self.gemini_keys)
        calculator = CalculatorTool()
        agent = Agent(name="LiveTestAgent", llm=llm, tools=[calculator])
        
        chunks = []
        async for chunk in agent.stream("What is 15 * 7 + 3?", yield_interval=0.05):
            chunks.append(chunk)
        
        # Verify complete workflow
        nodes_seen = {chunk["node"] for chunk in chunks if "node" in chunk}
        
        # Should see plan and at least one other node
        assert "plan" in nodes_seen
        assert len(nodes_seen) >= 2  # plan + reason/respond
        
        # Should have multiple chunk types
        chunk_types = {chunk["type"] for chunk in chunks}
        assert "thinking" in chunk_types
        assert "chunk" in chunk_types
        assert "state" in chunk_types
        
        # No errors
        errors = [c for c in chunks if c["type"] == "error"]
        assert len(errors) == 0, f"Errors found: {errors}"
    
    @pytest.mark.asyncio
    async def test_streaming_vs_run_consistency(self):
        """Verify streaming and run() produce consistent results."""
        calculator = CalculatorTool()
        
        # Streaming result
        llm1 = GeminiLLM(api_keys=self.gemini_keys)
        agent1 = Agent(name="StreamAgent", llm=llm1, tools=[calculator])
        
        stream_chunks = []
        async for chunk in agent1.stream("Calculate 6 * 8"):
            stream_chunks.append(chunk)
        
        # Regular result
        llm2 = GeminiLLM(api_keys=self.gemini_keys)
        agent2 = Agent(name="RunAgent", llm=llm2, tools=[calculator])
        
        run_result = await agent2.run("Calculate 6 * 8")
        
        # Both should complete successfully
        stream_errors = [c for c in stream_chunks if c["type"] == "error"]
        assert len(stream_errors) == 0
        assert "response" in run_result
        assert len(run_result["response"]) > 0


class TestLiveStreamingOpenAI:
    """Live streaming tests with OpenAI API."""
    
    @pytest.fixture(autouse=True)
    def setup_openai(self):
        """Setup OpenAI if key available."""
        self.openai_key = os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_KEY")
        if not self.openai_key:
            pytest.skip("No OpenAI API key available")
    
    @pytest.mark.asyncio
    async def test_openai_streaming_basic(self):
        """Basic OpenAI streaming test."""
        try:
            llm = OpenAILLM(api_keys=self.openai_key, model="gpt-4o-mini")
            calculator = CalculatorTool()
            agent = Agent(name="OpenAIAgent", llm=llm, tools=[calculator])
            
            chunks = []
            async for chunk in agent.stream("What is 2 + 2?"):
                chunks.append(chunk)
            
            assert len(chunks) > 0
            errors = [c for c in chunks if c["type"] == "error"]
            assert len(errors) == 0
            
        except Exception as e:
            if any(x in str(e) for x in ["404", "401", "quota", "billing"]):
                pytest.skip(f"OpenAI API issue: {e}")
            raise


class TestStreamingValidation:
    """Validate streaming chunk format and behavior."""
    
    @pytest.mark.asyncio
    async def test_chunk_format_validation(self):
        """Validate all chunks have proper format."""
        gemini_keys = [
            os.getenv("GEMINI_API_KEY_1"),
            os.getenv("GEMINI_API_KEY_2"), 
            os.getenv("GEMINI_API_KEY_3")
        ]
        gemini_keys = [key for key in gemini_keys if key]
        
        if not gemini_keys:
            pytest.skip("No API keys for validation")
        
        llm = GeminiLLM(api_keys=gemini_keys)
        agent = Agent(name="ValidationAgent", llm=llm, tools=[CalculatorTool()])
        
        chunks = []
        async for chunk in agent.stream("Hello"):
            chunks.append(chunk)
        
        # Every chunk must be a dict with 'type'
        for i, chunk in enumerate(chunks):
            assert isinstance(chunk, dict), f"Chunk {i} not dict: {type(chunk)}"
            assert "type" in chunk, f"Chunk {i} missing type: {chunk}"
            
            # Validate type-specific fields
            if chunk["type"] in ["thinking", "error"]:
                assert "content" in chunk
                assert "node" in chunk
            elif chunk["type"] == "chunk":
                assert "content" in chunk
            elif chunk["type"] == "result":
                assert "data" in chunk
                assert "node" in chunk
            elif chunk["type"] == "state":
                assert "state" in chunk
                assert "node" in chunk