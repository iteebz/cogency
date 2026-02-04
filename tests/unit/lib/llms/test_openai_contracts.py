from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from cogency.lib.llms import OpenAI
from cogency.lib.llms.openai import MAX_RECV_EVENTS, WS_CLOSE_TIMEOUT_SECONDS

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


def test_init_raises_without_api_key():
    with patch("cogency.lib.llms.openai.get_api_key", return_value=None):
        with pytest.raises(ValueError, match="No API key"):
            OpenAI()


def test_init_uses_provided_api_key():
    llm = OpenAI(api_key="explicit-key")
    assert llm.api_key == "explicit-key"


@pytest.mark.asyncio
async def test_generate_returns_empty_when_no_output():
    with patch("cogency.lib.llms.openai.get_api_key", return_value="test-key"):
        llm = OpenAI()

    mock_client = MagicMock()
    llm._create_client = MagicMock(return_value=mock_client)
    mock_client.responses.create = AsyncMock(return_value=MagicMock(output_text="", output=[]))

    with _rotation_calls_inner():
        result = await llm.generate([{"role": "user", "content": "x"}])
    assert result == ""


@pytest.mark.asyncio
async def test_generate_raises_import_error():
    with patch("cogency.lib.llms.openai.get_api_key", return_value="test-key"):
        llm = OpenAI()

    with (
        _rotation_calls_inner(),
        patch.object(llm, "_create_client", side_effect=ImportError("No openai")),
    ):
        with pytest.raises(ImportError):
            await llm.generate([{"role": "user", "content": "x"}])


@pytest.mark.asyncio
async def test_close_noop_for_http_instance():
    with patch("cogency.lib.llms.openai.get_api_key", return_value="test-key"):
        llm = OpenAI()
    await llm.close()


@pytest.mark.asyncio
async def test_close_exits_connection_manager():
    with patch("cogency.lib.llms.openai.get_api_key", return_value="test-key"):
        llm = OpenAI()

    mock_conn = MagicMock()
    mock_conn.close = AsyncMock()
    mock_manager = MagicMock()
    mock_manager.__aexit__ = AsyncMock()
    llm._connection = mock_conn
    llm._connection_manager = mock_manager

    await llm.close()

    mock_conn.close.assert_called_once()
    mock_manager.__aexit__.assert_called_once_with(None, None, None)
    assert llm._connection is None
    assert llm._connection_manager is None


@pytest.mark.asyncio
async def test_connect_configures_session():
    with patch("cogency.lib.llms.openai.get_api_key", return_value="test-key"):
        llm = OpenAI()

    mock_conn = MagicMock()
    mock_conn.session.update = AsyncMock()
    mock_conn.conversation.item.create = AsyncMock()

    mock_manager = MagicMock()
    mock_manager.__aenter__ = AsyncMock(return_value=mock_conn)
    mock_manager.__aexit__ = AsyncMock()

    mock_client = MagicMock()
    mock_client.api_key = "rotated-key"
    mock_client.realtime.connect = MagicMock(return_value=mock_manager)

    async def _rotation(_prefix, func, *args, **kwargs):
        return await func("test-key")

    messages = [
        {"role": "system", "content": "sys"},
        {"role": "user", "content": "u1"},
        {"role": "assistant", "content": "a1"},
    ]

    with (
        patch("cogency.lib.llms.openai.with_rotation", _rotation),
        patch.object(llm, "_create_client", return_value=mock_client),
    ):
        session = await llm.connect(messages)

    assert session._connection is mock_conn
    assert session._connection_manager is mock_manager
    mock_conn.session.update.assert_called_once()
    assert mock_conn.conversation.item.create.call_count == 2


@pytest.mark.asyncio
async def test_connect_raises_on_setup_failure():
    with patch("cogency.lib.llms.openai.get_api_key", return_value="test-key"):
        llm = OpenAI()

    mock_conn = MagicMock()
    mock_conn.session.update = AsyncMock(side_effect=Exception("fail"))

    mock_manager = MagicMock()
    mock_manager.__aenter__ = AsyncMock(return_value=mock_conn)
    mock_manager.__aexit__ = AsyncMock()

    mock_client = MagicMock()
    mock_client.realtime.connect = MagicMock(return_value=mock_manager)

    async def _rotation(_prefix, func, *args, **kwargs):
        return await func("test-key")

    with (
        patch("cogency.lib.llms.openai.with_rotation", _rotation),
        patch.object(llm, "_create_client", return_value=mock_client),
    ):
        with pytest.raises(RuntimeError, match="connection failed"):
            await llm.connect([{"role": "user", "content": "x"}])

    mock_manager.__aexit__.assert_called_once()


@pytest.mark.asyncio
async def test_connect_closes_existing_session():
    with patch("cogency.lib.llms.openai.get_api_key", return_value="test-key"):
        llm = OpenAI()

    old_manager = MagicMock()
    old_manager.__aexit__ = AsyncMock()
    old_conn = MagicMock()
    old_conn.close = AsyncMock()
    llm._connection_manager = old_manager
    llm._connection = old_conn

    mock_conn = MagicMock()
    mock_conn.session.update = AsyncMock()
    mock_conn.conversation.item.create = AsyncMock()

    mock_manager = MagicMock()
    mock_manager.__aenter__ = AsyncMock(return_value=mock_conn)

    mock_client = MagicMock()
    mock_client.api_key = "key"
    mock_client.realtime.connect = MagicMock(return_value=mock_manager)

    async def _rotation(_prefix, func, *args, **kwargs):
        return await func("test-key")

    with (
        patch("cogency.lib.llms.openai.with_rotation", _rotation),
        patch.object(llm, "_create_client", return_value=mock_client),
    ):
        await llm.connect([{"role": "user", "content": "x"}])

    old_conn.close.assert_called_once()


@pytest.mark.asyncio
async def test_send_without_connection_raises():
    with patch("cogency.lib.llms.openai.get_api_key", return_value="test-key"):
        llm = OpenAI()

    with pytest.raises(RuntimeError, match="requires active session"):
        async for _ in llm.send("hi"):
            pass


@pytest.mark.asyncio
async def test_send_raises_on_message_error():
    with patch("cogency.lib.llms.openai.get_api_key", return_value="test-key"):
        llm = OpenAI()

    conversation = MagicMock()
    conversation.item.create = AsyncMock(side_effect=Exception("msg fail"))
    llm._connection = MagicMock(conversation=conversation)

    with pytest.raises(Exception, match="msg fail"):
        async for _ in llm.send("content"):
            pass


@pytest.mark.asyncio
async def test_send_handles_timeout():
    with patch("cogency.lib.llms.openai.get_api_key", return_value="test-key"):
        llm = OpenAI()

    conversation = MagicMock()
    conversation.item.create = AsyncMock()
    response = MagicMock()
    response.create = AsyncMock()

    async def _timeout():
        raise TimeoutError()

    connection = MagicMock(conversation=conversation, response=response)
    connection.recv = _timeout
    llm._connection = connection

    with pytest.raises(RuntimeError, match="timeout"):
        async for _ in llm.send("x"):
            pass


@pytest.mark.asyncio
async def test_send_raises_on_unrecoverable_error_event():
    with patch("cogency.lib.llms.openai.get_api_key", return_value="test-key"):
        llm = OpenAI()

    conversation = MagicMock()
    conversation.item.create = AsyncMock()
    response = MagicMock()
    response.create = AsyncMock()

    error_event = MagicMock(type="error")
    error_event.code = "something_bad"

    connection = MagicMock(conversation=conversation, response=response)
    connection.recv = AsyncMock(return_value=error_event)
    llm._connection = connection

    with pytest.raises(RuntimeError, match="session error"):
        async for _ in llm.send("x"):
            pass


@pytest.mark.asyncio
async def test_send_tolerates_error_string_match():
    with patch("cogency.lib.llms.openai.get_api_key", return_value="test-key"):
        llm = OpenAI()

    conversation = MagicMock()
    conversation.item.create = AsyncMock()
    response = MagicMock()
    response.create = AsyncMock()

    error_event = type(
        "ErrorEvent",
        (),
        {"type": "error", "code": None, "__str__": lambda s: "already has an active response"},
    )()

    connection = MagicMock(conversation=conversation, response=response)
    connection.recv = AsyncMock(
        side_effect=[
            error_event,
            MagicMock(type="response.output_text.delta", delta="z"),
            MagicMock(type="response.done"),
        ]
    )
    llm._connection = connection

    chunks = []
    async for chunk in llm.send("x"):
        chunks.append(chunk)

    assert chunks == ["z"]


@pytest.mark.asyncio
async def test_send_handles_text_done_event():
    with patch("cogency.lib.llms.openai.get_api_key", return_value="test-key"):
        llm = OpenAI()

    conversation = MagicMock()
    conversation.item.create = AsyncMock()
    response = MagicMock()
    response.create = AsyncMock()

    connection = MagicMock(conversation=conversation, response=response)
    connection.recv = AsyncMock(
        side_effect=[
            MagicMock(type="response.output_text.delta", delta="a"),
            MagicMock(type="response.output_text.done"),
            MagicMock(type="response.done"),
        ]
    )
    llm._connection = connection

    chunks = []
    async for chunk in llm.send("x"):
        chunks.append(chunk)

    assert chunks == ["a"]


@pytest.mark.asyncio
async def test_send_logs_at_recv_ceiling():
    with patch("cogency.lib.llms.openai.get_api_key", return_value="test-key"):
        llm = OpenAI()

    conversation = MagicMock()
    conversation.item.create = AsyncMock()
    response = MagicMock()
    response.create = AsyncMock()

    connection = MagicMock(conversation=conversation, response=response)
    connection.recv = AsyncMock(return_value=MagicMock(type="other"))
    llm._connection = connection

    chunks = []
    async for chunk in llm.send("x"):
        chunks.append(chunk)
        if len(chunks) > MAX_RECV_EVENTS:
            break

    assert connection.recv.call_count == MAX_RECV_EVENTS


def test_constants_exist():
    assert MAX_RECV_EVENTS == 10000
    assert WS_CLOSE_TIMEOUT_SECONDS == 5.0
