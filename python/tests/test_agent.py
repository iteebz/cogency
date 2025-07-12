import json
from unittest.mock import AsyncMock, Mock, patch

import pytest

from cogency import Agent
from cogency.context import Context
from cogency.llm import GeminiLLM
from cogency.tools.calculator import CalculatorTool
from cogency.types import ExecutionTrace


class TestAgent:
    """Test suite for Agent class."""

    def setup_method(self):
        """Setup test fixtures."""
        self.mock_llm = AsyncMock(spec=GeminiLLM)
        response_payload = {"action": "direct_response", "answer": "Mocked response"}
        self.mock_llm.invoke.return_value = json.dumps(response_payload)
        self.calculator = CalculatorTool()

    def test_agent_initialization(self):
        """Test agent can be initialized with required parameters."""
        agent = Agent(name="TestAgent", llm=self.mock_llm)
        assert agent.name == "TestAgent"
        assert agent.llm == self.mock_llm
        assert agent.tools == []
        assert agent.workflow is not None
        assert agent.app is not None

    def test_agent_with_tools(self):
        """Test agent can be initialized with tools."""
        agent = Agent(name="TestAgent", llm=self.mock_llm, tools=[self.calculator])
        assert len(agent.tools) == 1
        assert agent.tools[0].name == "calculator"

    def test_agent_with_multiple_tools(self):
        """Test agent can handle multiple tools."""
        tool2 = Mock()
        tool2.name = "mock_tool"
        agent = Agent(name="TestAgent", llm=self.mock_llm, tools=[self.calculator, tool2])
        assert len(agent.tools) == 2
        assert agent.tools[0].name == "calculator"
        assert agent.tools[1].name == "mock_tool"

    def test_agent_workflow_structure(self):
        """Test that workflow is properly structured."""
        agent = Agent(name="TestAgent", llm=self.mock_llm)

        # Check that all required nodes are present
        nodes = list(agent.workflow.nodes.keys())
        expected_nodes = ["plan", "reason", "act", "reflect", "respond"]
        for node in expected_nodes:
            assert node in nodes

        # Check that the app is compiled
        assert agent.app is not None

    def test_plan_router_tool_needed(self):
        """Test plan router handles tool_needed response."""
        agent = Agent(name="TestAgent", llm=self.mock_llm)

        # Create mock state with tool_needed response
        context = Context(current_input="test")
        context.messages = [{"content": '{"action": "tool_needed", "reasoning": "need calc"}'}]
        state = {"context": context}

        result = agent._plan_router(state)
        assert result == "reason"

    def test_plan_router_direct_response(self):
        """Test plan router handles direct_response."""
        agent = Agent(name="TestAgent", llm=self.mock_llm)

        # Create mock state with direct response
        context = Context(current_input="test")
        context.messages = [{"content": '{"action": "direct_response", "answer": "42"}'}]
        state = {"context": context}

        result = agent._plan_router(state)
        assert result == "respond"

    def test_reflect_router_continue(self):
        """Test reflect router handles continue status."""
        agent = Agent(name="TestAgent", llm=self.mock_llm)

        # Create mock state with continue status
        context = Context(current_input="test")
        context.messages = [{"content": '{"status": "continue", "assessment": "need more"}'}]
        state = {"context": context}

        result = agent._reflect_router(state)
        assert result == "reason"

    def test_reflect_router_complete(self):
        """Test reflect router handles complete status."""
        agent = Agent(name="TestAgent", llm=self.mock_llm)

        # Create mock state with complete status
        context = Context(current_input="test")
        context.messages = [{"content": '{"status": "complete", "assessment": "done"}'}]
        state = {"context": context}

        result = agent._reflect_router(state)
        assert result == "respond"

    @patch("cogency.agent.uuid.uuid4")
    @pytest.mark.asyncio
    async def test_run_without_trace(self, mock_uuid):
        """Test agent run without trace enabled."""
        agent = Agent(name="TestAgent", llm=self.mock_llm)

        # Mock the entire workflow execution
        with patch.object(agent.app, "invoke") as mock_invoke:
            # Create a mock final state
            context = Context(current_input="test")
            response_payload = {
                "action": "direct_response",
                "answer": "Mocked response",
            }
            context.messages = [
                {
                    "role": "assistant",
                    "content": json.dumps(response_payload),
                }
            ]
            mock_final_state = {"context": context, "execution_trace": None}
            mock_invoke.return_value = mock_final_state

            result = await agent.run("Hello", enable_trace=False)

            assert "response" in result
            assert "conversation" in result
            assert "execution_trace" not in result
            assert result["response"] == "Mocked response"

    @patch("cogency.agent.uuid.uuid4")
    @pytest.mark.asyncio
    async def test_run_with_trace(self, mock_uuid):
        """Test agent run with trace enabled."""
        mock_uuid.return_value.hex = "abcd1234"

        agent = Agent(name="TestAgent", llm=self.mock_llm)

        # Mock the entire workflow execution
        with patch.object(agent.app, "invoke") as mock_invoke:
            # Create a mock final state with trace
            context = Context(current_input="test")
            response_payload = {
                "action": "direct_response",
                "answer": "Mocked response",
            }
            context.messages = [
                {
                    "role": "assistant",
                    "content": json.dumps(response_payload),
                }
            ]
            trace = ExecutionTrace(trace_id="abcd1234")
            mock_final_state = {"context": context, "execution_trace": trace}
            mock_invoke.return_value = mock_final_state

            result = await agent.run("Hello", enable_trace=True)

            assert "response" in result
            assert "conversation" in result
            assert "execution_trace" in result
            assert result["response"] == "Mocked response"

    @pytest.mark.asyncio
    async def test_run_empty_messages(self):
        """Test agent run with empty messages."""
        agent = Agent(name="TestAgent", llm=self.mock_llm)

        # Mock the workflow to return empty messages
        with patch.object(agent.app, "invoke") as mock_invoke:
            context = Context(current_input="test")
            response_payload = {
                "action": "direct_response",
                "answer": "Mocked response",
            }
            context.messages = [
                {
                    "role": "assistant",
                    "content": json.dumps(response_payload),
                }
            ]
            mock_final_state = {"context": context}
            mock_invoke.return_value = mock_final_state

            result = await agent.run("Hello")

            assert result["response"] == "Mocked response"

    @pytest.mark.asyncio
    async def test_agent_stream(self):
        """Test agent streaming functionality."""
        agent = Agent(name="TestAgent", llm=self.mock_llm)
        
        # Mock the streaming LLM
        async def mock_stream(messages, yield_interval=0.0):
            chunks = ["Hello", " streaming", " world"]
            for chunk in chunks:
                yield chunk
        
        self.mock_llm.stream = mock_stream
        
        chunks = []
        async for chunk in agent.stream("Hello"):
            chunks.append(chunk)
        
        # Should produce streaming chunks
        assert len(chunks) > 0
        assert any(chunk["type"] == "thinking" for chunk in chunks)

    @pytest.mark.asyncio
    async def test_agent_stream_with_yield_interval(self):
        """Test agent streaming with yield_interval parameter."""
        agent = Agent(name="TestAgent", llm=self.mock_llm)
        
        # Mock the streaming LLM
        async def mock_stream(messages, yield_interval=0.0):
            yield "test chunk"
        
        self.mock_llm.stream = mock_stream
        
        chunks = []
        async for chunk in agent.stream("Hello", yield_interval=0.1):
            chunks.append(chunk)
        
        # Should work with yield_interval parameter
        assert len(chunks) > 0
