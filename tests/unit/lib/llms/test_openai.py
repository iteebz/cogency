import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from cogency.lib.llms.openai import OpenAI

@pytest.fixture
def mock_with_rotation():
    with patch("cogency.lib.llms.openai.with_rotation") as mock_rotation:
        async def _side_effect(service, func):
            return await func("mock-api-key")
        mock_rotation.side_effect = _side_effect
        yield mock_rotation

@pytest.fixture
def mock_get_api_key():
    with patch("cogency.lib.rotation.get_api_key", return_value="test-key") as mock_get_key:
        yield mock_get_key

@pytest.mark.asyncio
async def test_openai_generate(mock_with_rotation, mock_get_api_key):
    openai_instance = OpenAI()

    with patch.object(openai_instance, "_create_client") as mock_create_client:
        mock_client_instance = mock_create_client.return_value
        # Mock the response from client.responses.create
        mock_response = MagicMock()
        mock_response.output = [MagicMock(content=[MagicMock(text="Generated text.")])]
        mock_client_instance.responses.create = AsyncMock(return_value=mock_response)

        messages = [{"role": "user", "content": "Test prompt"}]
        result = await openai_instance.generate(messages)

        mock_create_client.assert_called_once_with("mock-api-key")
        mock_client_instance.responses.create.assert_called_once_with(
            model=openai_instance.http_model,
            instructions="",
            input=[{"role": "user", "content": "Test prompt"}],
            temperature=openai_instance.temperature,
            stream=False,
        )
        assert result == "Generated text."

@pytest.mark.asyncio
async def test_openai_stream(mock_with_rotation, mock_get_api_key):
    openai_instance = OpenAI()

    with patch.object(openai_instance, "_create_client") as mock_create_client:
        mock_client_instance = mock_create_client.return_value
        # Mock streaming events
        mock_event_1 = MagicMock(type="response.output_text.delta", delta="Chunk 1")
        mock_event_2 = MagicMock(type="response.output_text.delta", delta="Chunk 2")
        mock_event_3 = MagicMock(type="response.output_text.delta", delta="Chunk 3")
        mock_event_done = MagicMock(type="response.completed") # Or response.output_text.done

        # Create an AsyncMock that can be iterated over asynchronously
        mock_stream_response = AsyncMock()
        mock_stream_response.__aiter__.return_value = iter([mock_event_1, mock_event_2, mock_event_3, mock_event_done])

        mock_client_instance.responses.create = AsyncMock(return_value=mock_stream_response)

        messages = [{"role": "user", "content": "Test stream prompt"}]
        
        collected_chunks = []
        async for chunk in openai_instance.stream(messages):
            collected_chunks.append(chunk)

        mock_create_client.assert_called_once_with("mock-api-key")
        mock_client_instance.responses.create.assert_called_once_with(
            model=openai_instance.http_model,
            instructions="",
            input=[{"role": "user", "content": "Test stream prompt"}],
            temperature=openai_instance.temperature,
            stream=True,
        )
        assert collected_chunks == ["Chunk 1", "Chunk 2", "Chunk 3"]