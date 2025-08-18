"""Test OpenAI provider implementation."""

from unittest.mock import AsyncMock, Mock

import pytest


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client."""
    client = Mock()
    client.chat = Mock()
    client.chat.completions = Mock()
    client.chat.completions.create = AsyncMock()

    client.embeddings = Mock()
    client.embeddings.create = AsyncMock()

    return client


@pytest.mark.asyncio
async def test_openai_generate_success(mock_openai_client):
    """OpenAI provider generates text successfully."""
    from cogency.lib.providers.openai import OpenAI

    # Mock successful response
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message = Mock()
    mock_response.choices[0].message.content = "Hello world"

    mock_openai_client.chat.completions.create.return_value = mock_response

    # Test provider
    provider = OpenAI(api_key="test-key")
    provider.client = mock_openai_client

    messages = [{"role": "user", "content": "Hello"}]
    result = await provider.generate(messages)

    assert result.success
    assert result.unwrap() == "Hello world"

    # Verify API call
    mock_openai_client.chat.completions.create.assert_called_once()


@pytest.mark.asyncio
async def test_openai_embed_success(mock_openai_client):
    """OpenAI provider embeds text successfully."""
    from cogency.lib.providers.openai import OpenAI

    # Mock successful response
    mock_response = Mock()
    mock_response.data = [Mock(), Mock()]
    mock_response.data[0].embedding = [0.1, 0.2, 0.3]
    mock_response.data[1].embedding = [0.4, 0.5, 0.6]

    mock_openai_client.embeddings.create.return_value = mock_response

    # Test provider
    provider = OpenAI(api_key="test-key")
    provider.client = mock_openai_client

    texts = ["Hello", "World"]
    result = await provider.embed(texts)

    assert result.success
    assert result.unwrap() == [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]

    # Verify API call
    mock_openai_client.embeddings.create.assert_called_once()


def test_openai_implements_protocols():
    """OpenAI provider implements required protocols."""
    from cogency.core.protocols import LLM, Embedder
    from cogency.lib.providers.openai import OpenAI

    provider = OpenAI(api_key="test-key")

    assert isinstance(provider, LLM)
    assert isinstance(provider, Embedder)
