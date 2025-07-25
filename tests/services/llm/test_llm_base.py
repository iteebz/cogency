"""Test BaseLLM - essential functionality only."""

import pytest

from cogency.services.llm.base import BaseLLM


class MockLLM(BaseLLM):
    def __init__(self, api_key=None, model="gpt-4"):
        super().__init__(provider_name="mock", api_keys=api_key or "test-key")
        self._model = model
        self.call_count = 0

    async def _run_impl(self, messages, **kwargs):
        self.call_count += 1
        if len(messages) == 0:
            return "No messages provided"
        return f"Mock response to: {messages[-1]['content']}"

    @property
    def model(self):
        return self._model

    async def stream(self, messages, **kwargs):
        response = f"Streaming response to: {messages[-1]['content']}"
        for word in response.split():
            yield word


def test_base_llm_abstract():
    """Test BaseLLM is abstract."""
    with pytest.raises(TypeError):
        BaseLLM("test-key")


@pytest.mark.asyncio
async def test_run_basic():
    """Test basic run functionality."""
    llm = MockLLM()
    messages = [{"role": "user", "content": "Hello"}]

    result = await llm.run(messages)
    assert result == "Mock response to: Hello"


@pytest.mark.asyncio
async def test_stream_basic():
    """Test basic streaming."""
    llm = MockLLM()
    messages = [{"role": "user", "content": "Hello"}]

    chunks = []
    async for chunk in llm.stream(messages):
        chunks.append(chunk)
    assert len(chunks) >= 2


def test_key_rotation():
    """Test key rotation functionality."""
    keys = ["key1", "key2", "key3"]
    llm = MockLLM(api_key=keys)

    # Test that key rotation works through KeyManager
    key1 = llm.next_key()
    key2 = llm.next_key()
    assert key1 in keys
    assert key2 in keys

    # Single key test
    llm_single = MockLLM(api_key="single-key")
    assert llm_single.next_key() == "single-key"


def test_model_property():
    """Test model property."""
    llm = MockLLM(model="custom-model")
    assert llm.model == "custom-model"
