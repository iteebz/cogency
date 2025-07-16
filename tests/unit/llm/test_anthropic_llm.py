
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import os
import asyncio

from cogency.llm.anthropic import AnthropicLLM
from cogency.llm.key_rotator import KeyRotator
from cogency.utils.errors import ConfigurationError

@pytest.fixture(autouse=True)
def cleanup_env_vars():
    """Clean up environment variables before each test."""
    original_anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    original_anthropic_key_1 = os.getenv("ANTHROPIC_API_KEY_1")

    if original_anthropic_key: del os.environ["ANTHROPIC_API_KEY"]
    if original_anthropic_key_1: del os.environ["ANTHROPIC_API_KEY_1"]

    yield

    if original_anthropic_key: os.environ["ANTHROPIC_API_KEY"] = original_anthropic_key
    if original_anthropic_key_1: os.environ["ANTHROPIC_API_KEY_1"] = original_anthropic_key_1

# --- Tests for AnthropicLLM (anthropic.py) ---

@patch('anthropic.AsyncAnthropic')
def test_anthropic_llm_init_single_key(mock_anthropic_async_client):
    """Test AnthropicLLM initializes with a single API key."""
    llm = AnthropicLLM(api_keys="test_key")
    mock_anthropic_async_client.assert_called_once_with(api_key="test_key")
    assert llm.api_key == "test_key"
    assert llm.key_rotator is None

@patch('anthropic.AsyncAnthropic')
def test_anthropic_llm_init_multiple_keys(mock_anthropic_async_client):
    """Test AnthropicLLM initializes with multiple API keys and a rotator."""
    llm = AnthropicLLM(api_keys=["key1", "key2"])
    assert llm.api_key is None
    assert isinstance(llm.key_rotator, KeyRotator)
    assert llm.key_rotator.keys == ["key1", "key2"]
    # Ensure client is initialized with the first key
    mock_anthropic_async_client.assert_called_once_with(api_key="key1")

@pytest.mark.asyncio
@patch('anthropic.AsyncAnthropic')
async def test_anthropic_llm_invoke(mock_anthropic_async_client):
    """Test AnthropicLLM invoke method calls Anthropic API correctly."""
    mock_client_instance = MagicMock()
    mock_anthropic_async_client.return_value = mock_client_instance
    
    # Mock the create method to be an AsyncMock
    mock_create = AsyncMock()
    mock_create.return_value.content = [MagicMock(text="Mocked Anthropic Response")]
    mock_client_instance.messages.create = mock_create

    llm = AnthropicLLM(api_keys="test_key")
    response = await llm.invoke([{"role": "user", "content": "Hello"}])

    assert response == "Mocked Anthropic Response"
    mock_create.assert_called_once_with(
        model="claude-3-5-sonnet-20241022",
        messages=[{"role": "user", "content": "Hello"}],
        timeout=15.0,
        temperature=0.7,
        max_tokens=4096,
        max_retries=3
    )

@pytest.mark.asyncio
@patch('anthropic.AsyncAnthropic')
async def test_anthropic_llm_stream(mock_anthropic_async_client):
    """Test AnthropicLLM stream method yields chunks correctly."""
    mock_client_instance = MagicMock()
    mock_anthropic_async_client.return_value = mock_client_instance

    # Mock the messages.stream method to return an AsyncMock
    mock_messages_stream = AsyncMock()
    mock_client_instance.messages.stream = mock_messages_stream

    # The object that __aenter__ will return (this is the 'stream' in 'async with ... as stream:')
    mock_context_manager_result = MagicMock()

    async def async_chunk_generator():
        yield "chunk1"
        yield "chunk2"
        yield "chunk3"

    mock_context_manager_result.text_stream = async_chunk_generator()

    # The object returned by mock_messages_stream() should be an AsyncMock
    # and its __aenter__ should return mock_context_manager_result
    mock_messages_stream.return_value.__aenter__.return_value = mock_context_manager_result

    llm = AnthropicLLM(api_keys="test_key")
    chunks = []
    async for chunk in llm.stream([{"role": "user", "content": "Stream me"}]):
        chunks.append(chunk)

    assert "".join(chunks) == "chunk1chunk2chunk3"
    mock_messages_stream.assert_called_once_with(
        model="claude-3-5-sonnet-20241022",
        messages=[{"role": "user", "content": "Stream me"}],
        timeout=15.0,
        temperature=0.7,
        max_tokens=4096,
        max_retries=3
    )
