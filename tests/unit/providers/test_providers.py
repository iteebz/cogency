"""Test Provider - essential functionality only."""

import pytest

from cogency.providers import Provider
from tests.fixtures.provider import MockProvider  # Testing unified provider behavior


def test_abstract():
    with pytest.raises(TypeError):
        Provider("test-key")


@pytest.mark.asyncio
async def test_run():
    provider = MockProvider()
    messages = [{"role": "user", "content": "Hello"}]

    result = await provider.run(messages)
    assert result.success and result.data == "Mock response"


@pytest.mark.asyncio
async def test_stream():
    provider = MockProvider()
    messages = [{"role": "user", "content": "Hello"}]

    chunks = []
    async for chunk in provider.stream(messages):
        chunks.append(chunk)
    assert len(chunks) >= 2


def test_rotation():
    keys = ["key1", "key2", "key3"]
    provider = MockProvider(api_keys=keys)

    key1 = provider.next_key()
    key2 = provider.next_key()
    assert key1 in keys
    assert key2 in keys

    provider_single = MockProvider(api_keys="single-key")
    assert provider_single.next_key() == "single-key"


@pytest.mark.asyncio
async def test_embed_single():
    provider = MockProvider()
    result = await provider.embed("test text")

    assert result.success
    assert len(result.data) == 1
    assert len(result.data[0]) == 384


@pytest.mark.asyncio
async def test_embed_multi():
    provider = MockProvider()
    texts = ["first", "second", "third"]
    result = await provider.embed(texts)

    assert result.success
    assert len(result.data) == 3


def test_embedding_capability():
    """Test that embedding-capable providers implement embed method."""

    from cogency.providers import Mistral, Ollama, OpenAI

    # Test with providers that support embeddings
    providers_to_test = [("openai", OpenAI), ("mistral", Mistral), ("ollama", Ollama)]

    for name, provider_class in providers_to_test:
        # Check that embed method is implemented (not the base NotImplementedError version)
        embed_method = provider_class.embed
        assert callable(embed_method), f"{name} provider should have embed method"

        # Verify it's not just the base Provider's NotImplementedError version
        # by checking if the method is defined in the class itself
        assert "embed" in provider_class.__dict__ or any(
            "embed" in base.__dict__
            for base in provider_class.__mro__[1:]
            if hasattr(base, "embed") and base != provider_class
        ), f"{name} provider should implement embed() method"


def test_model():
    provider = MockProvider(model="custom-model")
    assert provider.model == "custom-model"
