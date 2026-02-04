from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from cogency.lib.llms import Anthropic

if TYPE_CHECKING:
    from collections.abc import AsyncIterator


def _rotation_calls_inner():
    async def _with_rotation(_prefix, inner, *args, **kwargs):
        return await inner("test-key", *args, **kwargs)

    return patch("cogency.lib.llms.anthropic.with_rotation", _with_rotation)


def test_format_messages_splits_system():
    llm = Anthropic(api_key="test-key")

    system, conversation = llm._format_messages(
        [
            {"role": "system", "content": "a"},
            {"role": "user", "content": "u1"},
            {"role": "system", "content": "b"},
            {"role": "assistant", "content": "a1"},
        ]
    )

    assert system == "a\nb"
    assert conversation == [
        {"role": "user", "content": "u1"},
        {"role": "assistant", "content": "a1"},
    ]


def test_format_messages_empty_system():
    llm = Anthropic(api_key="test-key")

    system, conversation = llm._format_messages([{"role": "user", "content": "hi"}])

    assert system == ""
    assert conversation == [{"role": "user", "content": "hi"}]


def test_init_raises_without_api_key():
    with patch("cogency.lib.llms.rotation.get_api_key", return_value=None):
        with pytest.raises(ValueError, match="No Anthropic API key"):
            Anthropic()


def test_init_uses_provided_api_key():
    llm = Anthropic(api_key="explicit-key")
    assert llm.api_key == "explicit-key"


@pytest.mark.asyncio
async def test_generate_extracts_text():
    llm = Anthropic(api_key="test-key")

    mock_client = MagicMock()
    llm._create_client = MagicMock(return_value=mock_client)

    first_block = MagicMock()
    first_block.text = "hello"
    mock_response = MagicMock(content=[first_block])
    mock_client.messages.create = AsyncMock(return_value=mock_response)

    with _rotation_calls_inner():
        result = await llm.generate([{"role": "user", "content": "x"}])

    assert result == "hello"


@pytest.mark.asyncio
async def test_generate_returns_empty_when_no_text():
    llm = Anthropic(api_key="test-key")

    mock_client = MagicMock()
    llm._create_client = MagicMock(return_value=mock_client)

    first_block = MagicMock(spec=[])
    mock_response = MagicMock(content=[first_block])
    mock_client.messages.create = AsyncMock(return_value=mock_response)

    with _rotation_calls_inner():
        result = await llm.generate([{"role": "user", "content": "x"}])

    assert result == ""


@pytest.mark.asyncio
async def test_generate_raises_import_error():
    llm = Anthropic(api_key="test-key")

    with (
        _rotation_calls_inner(),
        patch.object(llm, "_create_client", side_effect=ImportError("No anthropic")),
    ):
        with pytest.raises(ImportError, match="anthropic"):
            await llm.generate([{"role": "user", "content": "x"}])


@pytest.mark.asyncio
async def test_stream_yields_text():
    llm = Anthropic(api_key="test-key")

    mock_client = MagicMock()
    llm._create_client = MagicMock(return_value=mock_client)

    async def _text_stream() -> AsyncIterator[str]:
        yield "a"
        yield "b"

    stream_obj = MagicMock()
    stream_obj.text_stream = _text_stream()

    mock_context = MagicMock()
    mock_context.__aenter__ = AsyncMock(return_value=stream_obj)
    mock_context.__aexit__ = AsyncMock()
    mock_client.messages.stream = MagicMock(return_value=mock_context)

    with _rotation_calls_inner():
        got = []
        async for chunk in llm.stream([{"role": "user", "content": "x"}]):
            got.append(chunk)
        assert got == ["a", "b"]


@pytest.mark.asyncio
async def test_connect_raises_not_implemented():
    llm = Anthropic(api_key="test-key")

    with pytest.raises(NotImplementedError, match="WebSocket"):
        await llm.connect([{"role": "user", "content": "x"}])


@pytest.mark.asyncio
async def test_send_raises_not_implemented():
    llm = Anthropic(api_key="test-key")

    with pytest.raises(NotImplementedError, match="WebSocket"):
        async for _ in llm.send("hi"):
            pass


@pytest.mark.asyncio
async def test_close_is_noop():
    llm = Anthropic(api_key="test-key")
    await llm.close()


def test_create_client_returns_async_anthropic():
    llm = Anthropic(api_key="test-key")

    with patch("anthropic.AsyncAnthropic") as mock_async:
        mock_client = MagicMock()
        mock_async.return_value = mock_client

        result = llm._create_client("rotated-key")

        mock_async.assert_called_once_with(api_key="rotated-key")
        assert result is mock_client
