import json
from unittest.mock import AsyncMock
from typing import AsyncIterator, Dict, Any

import pytest

from cogency.context import Context
from cogency.nodes.plan import plan_streaming
from cogency.nodes.reason import reason_streaming
from cogency.nodes.act import act_streaming
from cogency.nodes.respond import respond_streaming
from cogency.nodes.reflect import reflect_streaming
from cogency.tools.calculator import CalculatorTool


class MockLLM:
    """Mock LLM for testing streaming functions."""
    
    def __init__(self, response: str = "Mock response"):
        self.response = response
        
    async def stream(self, messages, yield_interval: float = 0.0) -> AsyncIterator[str]:
        """Stream mock response in chunks."""
        # Split response into chunks for realistic streaming
        chunks = self.response.split()
        for chunk in chunks:
            yield chunk + " "
        
    async def invoke(self, messages):
        """Non-streaming invoke for fallback."""
        return self.response


class TestStreamingNodes:
    """Test suite for streaming node functions."""

    def setup_method(self):
        """Setup test fixtures."""
        self.calculator = CalculatorTool()
        self.context = Context(current_input="What is 2 + 2?")
        self.state = {"context": self.context, "execution_trace": None}

    @pytest.mark.asyncio
    async def test_plan_streaming_direct_response(self):
        """Test plan_streaming with direct response."""
        response_json = '{"action": "direct_response", "answer": "Hello"}'
        mock_llm = MockLLM(response_json)
        
        chunks = []
        async for chunk in plan_streaming(self.state, mock_llm, [self.calculator]):
            chunks.append(chunk)
        
        # Verify chunk types
        chunk_types = [chunk["type"] for chunk in chunks]
        assert "thinking" in chunk_types
        assert "chunk" in chunk_types
        assert "result" in chunk_types
        assert "state" in chunk_types
        
        # Verify final state
        result_chunk = next(chunk for chunk in chunks if chunk["type"] == "result")
        assert "decision" in result_chunk["data"]

    @pytest.mark.asyncio
    async def test_plan_streaming_with_yield_interval(self):
        """Test plan_streaming respects yield_interval parameter."""
        mock_llm = MockLLM("test response")
        
        chunks = []
        async for chunk in plan_streaming(self.state, mock_llm, [], yield_interval=0.1):
            chunks.append(chunk)
        
        # Should still work with yield_interval (stub implementation)
        assert len(chunks) > 0
        assert any(chunk["type"] == "thinking" for chunk in chunks)

    @pytest.mark.asyncio
    async def test_reason_streaming_with_tools(self):
        """Test reason_streaming with tools."""
        tool_call = "TOOL_CALL: calculator(operation='add', x1=2, x2=2)"
        mock_llm = MockLLM(tool_call)
        
        chunks = []
        async for chunk in reason_streaming(self.state, mock_llm, [self.calculator]):
            chunks.append(chunk)
        
        # Verify chunk structure
        thinking_chunks = [c for c in chunks if c["type"] == "thinking"]
        assert len(thinking_chunks) >= 2  # Initial thinking + tool analysis
        
        # Verify tool information is included
        assert any("calculator" in str(chunk) for chunk in thinking_chunks)

    @pytest.mark.asyncio
    async def test_reason_streaming_without_tools(self):
        """Test reason_streaming without tools."""
        mock_llm = MockLLM("No tools available")
        
        chunks = []
        async for chunk in reason_streaming(self.state, mock_llm, []):
            chunks.append(chunk)
        
        # Should still produce chunks
        assert len(chunks) > 0
        assert any(chunk["type"] == "result" for chunk in chunks)

    @pytest.mark.asyncio
    async def test_act_streaming_successful_execution(self):
        """Test act_streaming with successful tool execution."""
        # Setup context with tool call
        tool_call = "TOOL_CALL: calculator(operation='add', x1=2, x2=2)"
        self.context.add_message("assistant", tool_call)
        
        chunks = []
        async for chunk in act_streaming(self.state, [self.calculator]):
            chunks.append(chunk)
        
        # Verify execution flow
        chunk_types = [chunk["type"] for chunk in chunks]
        assert "thinking" in chunk_types
        assert "tool_call" in chunk_types
        assert "result" in chunk_types
        assert "state" in chunk_types

    @pytest.mark.asyncio
    async def test_act_streaming_tool_not_found(self):
        """Test act_streaming when tool is not found."""
        # Setup context with unknown tool call
        tool_call = "TOOL_CALL: unknown_tool(arg=value)"
        self.context.add_message("assistant", tool_call)
        
        chunks = []
        async for chunk in act_streaming(self.state, [self.calculator]):
            chunks.append(chunk)
        
        # Should produce error chunks
        error_chunks = [c for c in chunks if c["type"] == "error"]
        assert len(error_chunks) > 0

    @pytest.mark.asyncio
    async def test_respond_streaming_direct_response(self):
        """Test respond_streaming with direct response JSON."""
        response_json = '{"action": "direct_response", "answer": "The answer is 4"}'
        self.context.add_message("assistant", response_json)
        
        chunks = []
        async for chunk in respond_streaming(self.state, MockLLM()):
            chunks.append(chunk)
        
        # Should process direct response without LLM call
        thinking_chunks = [c for c in chunks if c["type"] == "thinking"]
        assert any("direct response" in c["content"].lower() for c in thinking_chunks)

    @pytest.mark.asyncio
    async def test_respond_streaming_with_llm(self):
        """Test respond_streaming with LLM generation."""
        # Setup non-JSON message that requires LLM processing
        self.context.add_message("system", "Calculator result: 4")
        mock_llm = MockLLM("The answer is 4")
        
        chunks = []
        async for chunk in respond_streaming(self.state, mock_llm):
            chunks.append(chunk)
        
        # Should call LLM and stream response
        chunk_chunks = [c for c in chunks if c["type"] == "chunk"]
        assert len(chunk_chunks) > 0

    @pytest.mark.asyncio
    async def test_reflect_streaming_assessment(self):
        """Test reflect_streaming assessment generation."""
        mock_llm = MockLLM('{"status": "complete", "assessment": "Task completed"}')
        
        chunks = []
        async for chunk in reflect_streaming(self.state, mock_llm):
            chunks.append(chunk)
        
        # Verify assessment flow
        chunk_types = [chunk["type"] for chunk in chunks]
        assert "thinking" in chunk_types
        assert "chunk" in chunk_types
        assert "result" in chunk_types
        assert "state" in chunk_types

    @pytest.mark.asyncio
    async def test_streaming_yield_interval_parameters(self):
        """Test that all streaming functions accept yield_interval parameter."""
        mock_llm = MockLLM("test")
        yield_interval = 0.05
        
        # Test all streaming functions accept the parameter
        functions_to_test = [
            (plan_streaming, [self.state, mock_llm, []]),
            (reason_streaming, [self.state, mock_llm, []]),
            (act_streaming, [self.state, []]),
            (respond_streaming, [self.state, mock_llm]),
            (reflect_streaming, [self.state, mock_llm])
        ]
        
        for func, args in functions_to_test:
            chunks = []
            async for chunk in func(*args, yield_interval=yield_interval):
                chunks.append(chunk)
            
            # Each function should produce at least some chunks
            assert len(chunks) > 0

    @pytest.mark.asyncio
    async def test_streaming_chunk_structure(self):
        """Test that streaming chunks have consistent structure."""
        mock_llm = MockLLM("test response")
        
        chunks = []
        async for chunk in plan_streaming(self.state, mock_llm, []):
            chunks.append(chunk)
        
        # Verify all chunks have required fields
        for chunk in chunks:
            assert isinstance(chunk, dict)
            assert "type" in chunk
            assert "node" in chunk
            
            # Verify type-specific fields
            if chunk["type"] == "thinking":
                assert "content" in chunk
            elif chunk["type"] == "chunk":
                assert "content" in chunk
            elif chunk["type"] == "result":
                assert "data" in chunk
            elif chunk["type"] == "state":
                assert "state" in chunk