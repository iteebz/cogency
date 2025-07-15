"""BaseLLM primitive test - ZERO BULLSHIT."""
import pytest
from cogency.llm.base import BaseLLM


class SimpleLLM(BaseLLM):
    async def invoke(self, messages, **kwargs):
        return "test response"
    
    async def stream(self, messages, **kwargs):
        for char in "test":
            yield char


class TestBaseLLM:
    @pytest.mark.asyncio
    async def test_llm_interface(self):
        """BaseLLM has required interface."""
        llm = SimpleLLM()
        
        response = await llm.invoke([])
        assert response == "test response"
        
        chunks = []
        async for chunk in llm.stream([]):
            chunks.append(chunk)
        assert "".join(chunks) == "test"