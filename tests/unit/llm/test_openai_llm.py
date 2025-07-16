import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import os
import asyncio

from cogency.llm.openai import OpenAILLM
from cogency.llm.key_rotator import KeyRotator
from cogency.utils.errors import ConfigurationError

@pytest.fixture(autouse=True)
def cleanup_env_vars():
    """Clean up environment variables before each test."""
    original_openai_key = os.getenv("OPENAI_API_KEY")
    original_openai_key_1 = os.getenv("OPENAI_API_KEY_1")

    if original_openai_key: del os.environ["OPENAI_API_KEY"]
    if original_openai_key_1: del os.environ["OPENAI_API_KEY_1"]

    yield

    if original_openai_key: os.environ["OPENAI_API_KEY"] = original_openai_key
    if original_openai_key_1: os.environ["OPENAI_API_KEY_1"] = original_openai_key_1

# --- Tests for OpenAILLM (openai.py) ---

@patch('openai.AsyncOpenAI')
def test_openai_llm_init_single_key(mock_openai_async_client):
    """Test OpenAILLM initializes with a single API key."""
    llm = OpenAILLM(api_keys="test_key")
    mock_openai_async_client.assert_called_once_with(api_key="test_key", timeout=15.0, max_retries=3)
    assert llm.api_key == "test_key"
    assert llm.key_rotator is None

@patch('openai.AsyncOpenAI')
def test_openai_llm_init_multiple_keys(mock_openai_async_client):
    """Test OpenAILLM initializes with multiple API keys and a rotator."""
    llm = OpenAILLM(api_keys=["key1", "key2"])
    assert llm.api_key is None
    assert isinstance(llm.key_rotator, KeyRotator)
    assert llm.key_rotator.keys == ["key1", "key2"]
    # Ensure client is initialized with the first key
    mock_openai_async_client.assert_called_once_with(api_key="key1", timeout=15.0, max_retries=3)

@pytest.mark.asyncio
@patch('openai.AsyncOpenAI')
async def test_openai_llm_invoke(mock_openai_async_client):
    """Test OpenAILLM invoke method calls OpenAI API correctly."""
    mock_client_instance = MagicMock()
    mock_openai_async_client.return_value = mock_client_instance
    
    # Mock the create method to be an AsyncMock
    mock_create = AsyncMock()
    mock_create.return_value.choices = [MagicMock(message=MagicMock(content="Mocked OpenAI Response"))]
    mock_client_instance.chat.completions.create = mock_create

    llm = OpenAILLM(api_keys="test_key")
    response = await llm.invoke([{"role": "user", "content": "Hello"}])

    assert response == "Mocked OpenAI Response"
    mock_create.assert_called_once_with(
        model="gpt-4o",
        messages=[{"role": "user", "content": "Hello"}],
        temperature=0.7
    )

@pytest.mark.asyncio
@patch('openai.AsyncOpenAI')
async def test_openai_llm_stream(mock_openai_async_client):
    """Test OpenAILLM stream method yields chunks correctly."""
    mock_client_instance = MagicMock()
    mock_openai_async_client.return_value = mock_client_instance

    # Mock the async generator for stream
    async def mock_stream_response():
        yield MagicMock(choices=[MagicMock(delta=MagicMock(content="chunk1"))])
        yield MagicMock(choices=[MagicMock(delta=MagicMock(content="chunk2"))])
        yield MagicMock(choices=[MagicMock(delta=MagicMock(content="chunk3"))])

    # Mock the create method to be an AsyncMock that returns the async generator
    mock_create_stream = AsyncMock(return_value=mock_stream_response())
    mock_client_instance.chat.completions.create = mock_create_stream

    llm = OpenAILLM(api_keys="test_key")
    chunks = []
    async for chunk in llm.stream([{"role": "user", "content": "Stream me"}]):
        chunks.append(chunk)

    assert "".join(chunks) == "chunk1chunk2chunk3"
    mock_create_stream.assert_called_once_with(
        model="gpt-4o",
        messages=[{"role": "user", "content": "Stream me"}],
        stream=True,
        temperature=0.7
    )