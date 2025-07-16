
import pytest
import asyncio
from cogency.llm.mock import MockLLM

@pytest.mark.asyncio
async def test_mock_llm_invoke():
    """Test MockLLM invoke method returns the predefined response."""
    llm = MockLLM(response="Hello from MockLLM")
    response = await llm.invoke([{"role": "user", "content": "test"}])
    assert response == "Hello from MockLLM"

@pytest.mark.asyncio
async def test_mock_llm_stream():
    """Test MockLLM stream method yields the predefined response character by character."""
    llm = MockLLM(response="Streamed response")
    chunks = []
    async for chunk in llm.stream([{"role": "user", "content": "test"}]):
        chunks.append(chunk)
    assert "".join(chunks) == "Streamed response"
