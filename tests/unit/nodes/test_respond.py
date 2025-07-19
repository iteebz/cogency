"""Tests for respond node - final response formatting and personality."""
import pytest
from unittest.mock import Mock, AsyncMock

from cogency.nodes.respond import respond_node, build_response_prompt
from cogency.common.types import AgentState, ReasoningDecision
from cogency.context import Context


class TestRespondNode:
    """Test respond node functionality."""

    @pytest.fixture
    def mock_llm(self):
        """Mock LLM."""
        llm = AsyncMock()
        llm.invoke = AsyncMock(return_value="Final response")
        return llm

    @pytest.fixture
    def sample_state(self):
        """Sample agent state.""" 
        context = Context(user_id="test_user")
        context.current_input = "Test query"
        context.messages = [{"role": "user", "content": "Hello"}]
        
        return {
            "query": "Test query",
            "context": context
        }

    def test_build_response_prompt_basic(self):
        """Test basic response prompt building."""
        prompt = build_response_prompt()
        assert "Generate final response" in prompt
        assert "conversational" in prompt

    def test_build_response_prompt_with_system(self):
        """Test response prompt with system prompt."""
        system_prompt = "You are a helpful assistant."
        prompt = build_response_prompt(system_prompt)
        assert system_prompt in prompt
        assert "Generate final response" in prompt

    @pytest.mark.asyncio
    async def test_respond_direct_bypass(self, sample_state, mock_llm):
        """Test respond node with direct bypass from preprocess."""
        sample_state["direct_response_bypass"] = True
        
        result = await respond_node(
            sample_state,
            llm=mock_llm
        )
        
        assert result["next_node"] == "END"
        assert "reasoning_decision" in result
        assert result["reasoning_decision"].task_complete is True
        assert "last_node_output" in result

    @pytest.mark.asyncio
    async def test_respond_with_direct_response(self, sample_state, mock_llm):
        """Test respond node with direct response from reasoning."""
        sample_state["direct_response"] = "Direct reasoning response"
        
        result = await respond_node(
            sample_state,
            llm=mock_llm,
            system_prompt="Be helpful"
        )
        
        assert result["next_node"] == "END"
        assert result["reasoning_decision"].task_complete is True
        mock_llm.invoke.assert_called_once()

    @pytest.mark.asyncio
    async def test_respond_formats_final_response(self, sample_state, mock_llm):
        """Test respond node formats final response."""
        result = await respond_node(
            sample_state,
            llm=mock_llm,
            response_shaper={"profile": "concise"}
        )
        
        assert "last_node_output" in result
        assert result["reasoning_decision"].should_respond is True
        mock_llm.invoke.assert_called_once()