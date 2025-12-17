from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from cogency.lib.llms import Gemini, OpenAI


@pytest.fixture(
    params=[
        pytest.param(("OpenAI", OpenAI, "cogency.lib.llms.openai.get_api_key"), id="openai"),
        pytest.param(("Gemini", Gemini, "cogency.lib.llms.gemini.get_api_key"), id="gemini"),
    ]
)
def llm_instance(request):
    """Provides an instance of each LLM provider with a mocked API key."""
    name, cls, patch_path = request.param
    with patch(patch_path, return_value="test-key"):
        instance = cls()
        yield name, instance


@pytest.mark.asyncio
async def test_llm_generate(llm_instance):
    """Tests the generate method of each LLM provider."""
    name, llm_instance = llm_instance

    async def mock_rotation(prefix, func, *args, **kwargs):
        return await func("test-key")

    with (
        patch.object(llm_instance, "_create_client") as mock_create_client,
        patch("cogency.lib.llms.openai.with_rotation", mock_rotation),
        patch("cogency.lib.llms.gemini.with_rotation", mock_rotation),
    ):
        mock_client_instance = mock_create_client.return_value
        mock_response = MagicMock()  # Make mock_response a MagicMock

        if name == "OpenAI":
            mock_response.output_text = "Generated text."
            mock_client_instance.responses.create = AsyncMock(return_value=mock_response)
        elif name == "Gemini":
            mock_response.text = "Generated text."
            mock_client_instance.aio.models.generate_content = AsyncMock(return_value=mock_response)
        elif name == "Anthropic":
            mock_response.content = [MagicMock(text="Generated text.")]
            mock_client_instance.messages.create = AsyncMock(return_value=mock_response)
        else:
            raise ValueError(f"Unknown LLM provider: {name}")

        messages = [{"role": "user", "content": "Test prompt"}]
        result = await llm_instance.generate(messages)

        assert result == "Generated text."


@pytest.mark.asyncio
async def test_llm_stream(llm_instance):
    """Tests the stream method of each LLM provider."""
    name, llm_instance = llm_instance

    async def mock_rotation(prefix, func, *args, **kwargs):
        return await func("test-key")

    with (
        patch.object(llm_instance, "_create_client") as mock_create_client,
        patch("cogency.lib.llms.openai.with_rotation", mock_rotation),
        patch("cogency.lib.llms.gemini.with_rotation", mock_rotation),
    ):
        mock_client_instance = mock_create_client.return_value
        mock_stream_response = AsyncMock()

        def _create_mock_chunk(provider_name, content):
            if provider_name == "OpenAI":
                chunk = MagicMock()
                chunk.type = "response.output_text.delta"
                chunk.delta = content
                return chunk
            if provider_name == "Gemini":
                return MagicMock(text=content)
            if provider_name == "Anthropic":
                return content
            raise ValueError(f"Unknown provider for mock chunk: {provider_name}")

        if name == "OpenAI":
            mock_chunk_1 = _create_mock_chunk(name, "Chunk 1")
            mock_chunk_2 = _create_mock_chunk(name, "Chunk 2")
            # Create end event
            mock_end_event = MagicMock()
            mock_end_event.type = "response.done"

            async def _async_stream_iter():
                yield mock_chunk_1
                yield mock_chunk_2
                yield mock_end_event

            mock_stream_response = AsyncMock()
            mock_stream_response.__aiter__ = lambda self: _async_stream_iter()
            mock_client_instance.responses.create = AsyncMock(return_value=mock_stream_response)
        elif name == "Gemini":
            mock_chunk_1 = _create_mock_chunk(name, "Chunk 1")
            mock_chunk_2 = _create_mock_chunk(name, "Chunk 2")

            mock_stream_response = AsyncMock()  # Make mock_stream_response an AsyncMock
            mock_stream_response.__aiter__.return_value = iter([mock_chunk_1, mock_chunk_2])
            mock_client_instance.aio.models.generate_content_stream = AsyncMock(
                return_value=mock_stream_response
            )
        elif name == "Anthropic":
            mock_chunk_1 = _create_mock_chunk(name, "Chunk 1")
            mock_chunk_2 = _create_mock_chunk(name, "Chunk 2")

            mock_stream_response_inner = AsyncMock()  # This is the actual async context manager
            mock_stream_response_inner.text_stream = AsyncMock()
            mock_stream_response_inner.text_stream.__aiter__.return_value = iter(
                [mock_chunk_1, mock_chunk_2]
            )
            mock_stream_response_inner.__aenter__.return_value = mock_stream_response_inner
            mock_stream_response_inner.__aexit__.return_value = None

            mock_client_instance.messages.stream = AsyncMock(
                return_value=mock_stream_response_inner
            )
        else:
            raise ValueError(f"Unknown LLM provider: {name}")

        messages = [{"role": "user", "content": "Test stream prompt"}]
        collected_chunks = []
        async for chunk in llm_instance.stream(messages):
            collected_chunks.append(chunk)

        assert collected_chunks == ["Chunk 1", "Chunk 2"]


@pytest.fixture(
    params=[
        pytest.param(("OpenAI", OpenAI, "cogency.lib.llms.openai.get_api_key"), id="openai"),
        pytest.param(("Gemini", Gemini, "cogency.lib.llms.gemini.get_api_key"), id="gemini"),
    ]
)
def websocket_llm_instance(request):
    """Provides an instance of WebSocket-capable LLM providers with a mocked API key."""
    name, cls, patch_path = request.param
    with patch(patch_path, return_value="test-key"):
        instance = cls()
        yield name, instance


@pytest.mark.asyncio
async def test_websocket_methods(websocket_llm_instance):
    """Tests connect, send, and close methods for WebSocket-capable LLM providers."""
    _name, llm_instance = websocket_llm_instance

    # Mock the connect method of the llm_instance directly
    with patch.object(llm_instance, "connect") as mock_llm_connect:
        mock_session = MagicMock()
        mock_session.send = AsyncMock()
        mock_session.close = AsyncMock()
        mock_llm_connect.return_value = mock_session

        # Test connect
        session = await llm_instance.connect([{"role": "user", "content": "initial message"}])
        mock_llm_connect.assert_called_once()
        assert session is not None

    # Test send
    await session.send("test message")
    mock_session.send.assert_called_once_with("test message")

    # Test close
    await session.close()
    mock_session.close.assert_called_once()
