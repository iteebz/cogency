from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from cogency.lib.llms import OpenAI

if TYPE_CHECKING:
    from collections.abc import AsyncIterator


def _rotation_calls_inner():
    async def _with_rotation(_prefix, inner, *args, **kwargs):
        return await inner("test-key", *args, **kwargs)

    return patch("cogency.lib.llms.openai.with_rotation", _with_rotation)


def test_format_messages_contract():
    with patch("cogency.lib.llms.openai.get_api_key", return_value="test-key"):
        llm = OpenAI()

    instructions, input_messages = llm._format_messages(
        [
            {"role": "system", "content": "a"},
            {"role": "user", "content": "u1"},
            {"role": "tool", "content": "t1"},
            {"role": "system", "content": "b"},
            {"role": "assistant", "content": "a1"},
        ]
    )

    assert instructions == "a\nb"
    assert input_messages == [
        {"role": "user", "content": "u1"},
        {"role": "user", "content": "t1"},
        {"role": "assistant", "content": "a1"},
    ]


@pytest.mark.asyncio
async def test_generate_prefers_output_text():
    with patch("cogency.lib.llms.openai.get_api_key", return_value="test-key"):
        llm = OpenAI()

    mock_client = MagicMock()
    llm._create_client = MagicMock(return_value=mock_client)
    mock_client.responses.create = AsyncMock(return_value=MagicMock(output_text="hi"))

    with _rotation_calls_inner():
        assert await llm.generate([{"role": "user", "content": "x"}]) == "hi"


@pytest.mark.asyncio
async def test_generate_falls_back_to_output_blocks():
    with patch("cogency.lib.llms.openai.get_api_key", return_value="test-key"):
        llm = OpenAI()

    mock_client = MagicMock()
    llm._create_client = MagicMock(return_value=mock_client)

    first_content = MagicMock()
    first_content.text = "fallback"
    output_msg = MagicMock(content=[first_content])
    response = MagicMock(output_text="", output=[output_msg])
    mock_client.responses.create = AsyncMock(return_value=response)

    with _rotation_calls_inner():
        assert await llm.generate([{"role": "user", "content": "x"}]) == "fallback"


@pytest.mark.asyncio
async def test_stream_yields_only_text_deltas():
    with patch("cogency.lib.llms.openai.get_api_key", return_value="test-key"):
        llm = OpenAI()

    mock_client = MagicMock()
    llm._create_client = MagicMock(return_value=mock_client)

    async def _aiter() -> AsyncIterator[object]:
        yield MagicMock(type="response.output_text.delta", delta="a")
        yield MagicMock(type="response.output_text.delta", delta="b")
        yield MagicMock(type="response.done")

    stream_obj = MagicMock()
    stream_obj.__aiter__ = lambda self: _aiter()
    mock_client.responses.create = AsyncMock(return_value=stream_obj)

    with _rotation_calls_inner():
        got = []
        async for chunk in llm.stream([{"role": "user", "content": "x"}]):
            got.append(chunk)
        assert got == ["a", "b"]


@pytest.mark.asyncio
async def test_stream_accepts_legacy_delta_events():
    with patch("cogency.lib.llms.openai.get_api_key", return_value="test-key"):
        llm = OpenAI()

    mock_client = MagicMock()
    llm._create_client = MagicMock(return_value=mock_client)

    async def _aiter() -> AsyncIterator[object]:
        yield type("LegacyDelta", (), {"delta": "a"})()
        yield type("LegacyDelta", (), {"delta": "b"})()

    stream_obj = MagicMock()
    stream_obj.__aiter__ = lambda self: _aiter()
    mock_client.responses.create = AsyncMock(return_value=stream_obj)

    with _rotation_calls_inner():
        got = []
        async for chunk in llm.stream([{"role": "user", "content": "x"}]):
            got.append(chunk)
        assert got == ["a", "b"]


@pytest.mark.asyncio
async def test_send_yields_until_done():
    with patch("cogency.lib.llms.openai.get_api_key", return_value="test-key"):
        llm = OpenAI()

    conversation = MagicMock()
    conversation.item.create = AsyncMock()
    response = MagicMock()
    response.create = AsyncMock()

    events = [
        MagicMock(type="response.output_text.delta", delta="a"),
        MagicMock(type="response.output_text.delta", delta="b"),
        MagicMock(type="response.done"),
    ]
    connection = MagicMock(conversation=conversation, response=response)
    connection.recv = AsyncMock(side_effect=events)
    llm._connection = connection

    got = []
    async for chunk in llm.send("hello"):
        got.append(chunk)

    assert got == ["a", "b"]
    conversation.item.create.assert_called_once()
    response.create.assert_called_once()


@pytest.mark.asyncio
async def test_send_tolerates_active_response_on_create():
    with patch("cogency.lib.llms.openai.get_api_key", return_value="test-key"):
        llm = OpenAI()

    conversation = MagicMock()
    conversation.item.create = AsyncMock()
    response = MagicMock()
    response.create = AsyncMock(side_effect=Exception("already has an active response"))

    connection = MagicMock(conversation=conversation, response=response)
    connection.recv = AsyncMock(
        side_effect=[
            MagicMock(type="response.output_text.delta", delta="a"),
            MagicMock(type="response.done"),
        ]
    )
    llm._connection = connection

    got = []
    async for chunk in llm.send(""):
        got.append(chunk)

    assert got == ["a"]
    conversation.item.create.assert_not_called()


@pytest.mark.asyncio
async def test_send_prefers_error_code_over_string_match():
    with patch("cogency.lib.llms.openai.get_api_key", return_value="test-key"):
        llm = OpenAI()

    conversation = MagicMock()
    conversation.item.create = AsyncMock()
    response = MagicMock()

    class ErrorWithCodeError(Exception):
        code = "active_response_exists"

    response.create = AsyncMock(side_effect=ErrorWithCodeError())

    connection = MagicMock(conversation=conversation, response=response)
    connection.recv = AsyncMock(
        side_effect=[
            MagicMock(type="response.output_text.delta", delta="x"),
            MagicMock(type="response.done"),
        ]
    )
    llm._connection = connection

    chunks = []
    async for chunk in llm.send(""):
        chunks.append(chunk)

    assert chunks == ["x"]


@pytest.mark.asyncio
async def test_send_tolerates_active_response_error_event():
    with patch("cogency.lib.llms.openai.get_api_key", return_value="test-key"):
        llm = OpenAI()

    conversation = MagicMock()
    conversation.item.create = AsyncMock()
    response = MagicMock()
    response.create = AsyncMock()

    error_event = MagicMock(type="error")
    error_event.code = "active_response_exists"

    connection = MagicMock(conversation=conversation, response=response)
    connection.recv = AsyncMock(
        side_effect=[
            error_event,
            MagicMock(type="response.output_text.delta", delta="y"),
            MagicMock(type="response.done"),
        ]
    )
    llm._connection = connection

    chunks = []
    async for chunk in llm.send("test"):
        chunks.append(chunk)

    assert chunks == ["y"]
