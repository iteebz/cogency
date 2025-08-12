"""Test Provider - updated for canonical generate() interface."""

import pytest
from tests.fixtures import mock_provider

from cogency.providers import Provider


def test_abstract():
    """Test that Provider is abstract and cannot be instantiated directly."""
    with pytest.raises(TypeError):
        Provider("test-key")


@pytest.mark.asyncio
async def test_generate():
    """Test LLM generation with canonical interface."""
    provider = mock_provider("Mock response")
    messages = [{"role": "user", "content": "Hello"}]

    result = await provider.generate(messages)
    assert result.success and result.data == "Mock response"


@pytest.mark.asyncio
async def test_stream():
    """Test streaming generation."""
    provider = mock_provider("Mock response")
    messages = [{"role": "user", "content": "Hello"}]

    chunks = []
    async for chunk in provider.stream(messages):
        chunks.append(chunk)
    assert len(chunks) >= 2


def test_rotation():
    """Test API key rotation."""
    keys = ["key1", "key2", "key3"]
    provider = mock_provider("Mock response", api_keys=keys)

    key1 = provider.next_key()
    key2 = provider.next_key()
    assert key1 in keys
    assert key2 in keys

    provider_single = mock_provider("Mock response", api_keys="single-key")
    assert provider_single.next_key() == "single-key"


@pytest.mark.asyncio
async def test_embed_single():
    """Test single text embedding."""
    provider = mock_provider("Mock response")
    result = await provider.embed("test text")
    assert result.success
    assert isinstance(result.data, list)
    assert len(result.data) > 0


@pytest.mark.asyncio
async def test_embed_batch():
    """Test batch text embedding."""
    provider = mock_provider("Mock response")
    texts = ["text 1", "text 2", "text 3"]
    
    result = await provider.embed(texts)
    assert result.success
    assert isinstance(result.data, list)
    assert len(result.data) == len(texts)
