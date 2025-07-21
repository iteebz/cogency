"""Test BaseLLM - essential functionality only."""
import pytest
from cogency.llm.base import BaseLLM


class MockLLM(BaseLLM):
    def __init__(self, api_key=None, model="gpt-4"):
        self._model = model
        self.call_count = 0
        self._api_key = api_key or "test-key"
        self.provider_name = "mock"
        self._current_key_index = 0
    
    async def run(self, messages, **kwargs):
        self.call_count += 1
        if len(messages) == 0:
            return "No messages provided"
        return f"Mock response to: {messages[-1]['content']}"
    
    def stream(self, messages, **kwargs):
        response = f"Streaming response to: {messages[-1]['content']}"
        for chunk in response.split():
            yield chunk
    
    @property
    def model(self):
        return self._model
    
    def rotate_key(self):
        if isinstance(self._api_key, list) and len(self._api_key) > 1:
            self._current_key_index = (self._current_key_index + 1) % len(self._api_key)
    
    @property
    def current_key(self):
        if isinstance(self._api_key, list):
            return self._api_key[self._current_key_index]
        return self._api_key
    
    @property
    def api_key(self):
        return self._api_key


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
    assert "Mock response to: Hello" == result


def test_stream_basic():
    """Test basic streaming."""
    llm = MockLLM()
    messages = [{"role": "user", "content": "Hello"}]
    
    chunks = list(llm.stream(messages))
    assert len(chunks) >= 2


def test_key_rotation():
    """Test key rotation functionality."""
    keys = ["key1", "key2", "key3"]
    llm = MockLLM(api_key=keys)
    
    assert llm.current_key == "key1"
    llm.rotate_key()
    assert llm.current_key == "key2"
    
    # Single key does nothing
    llm_single = MockLLM(api_key="single-key")
    original = llm_single.current_key
    llm_single.rotate_key()
    assert llm_single.current_key == original


def test_model_property():
    """Test model property."""
    llm = MockLLM(model="custom-model")
    assert llm.model == "custom-model"