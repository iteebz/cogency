import pytest
import asyncio
from cogency.llm.mock import MockLLM

@pytest.mark.asyncio
async def test_mock_llm_invoke():
    """Test MockLLM invoke method returns the predefined response."""
    mock_response = "Hello from MockLLM"
    llm = MockLLM(response=mock_response)
    result = await llm.invoke(messages=[])
    assert result == mock_response

@pytest.mark.asyncio
async def test_mock_llm_stream():
    """Test MockLLM stream method yields characters of the predefined response."""
    mock_response = "Streamed response"
    llm = MockLLM(response=mock_response)
    streamed_chars = []
    async for char in llm.stream(messages=[]):
        streamed_chars.append(char)
    assert "".join(streamed_chars) == mock_response
