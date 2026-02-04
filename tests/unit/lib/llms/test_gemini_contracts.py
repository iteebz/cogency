from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from cogency.lib.llms import Gemini
from cogency.lib.llms.gemini import MAX_SESSION_MESSAGES


def _server_content(*, text: str | None = None, generation_complete=False, turn_complete=False):
    model_turn = None
    if text is not None:
        part = type("Part", (), {"text": text})
        model_turn = type("ModelTurn", (), {"parts": [part]})
    return type(
        "ServerContent",
        (),
        {
            "model_turn": model_turn,
            "generation_complete": generation_complete,
            "turn_complete": turn_complete,
        },
    )()


def _message(server_content):
    return type("Message", (), {"server_content": server_content})()


@pytest.mark.asyncio
async def test_send_requires_dual_signals_to_terminate():
    with patch("cogency.lib.llms.gemini.get_api_key", return_value="test-key"):
        llm = Gemini()

    llm._session = MagicMock()
    llm._session.send_client_content = AsyncMock()

    async def _receive():
        yield _message(_server_content(text="a", generation_complete=True, turn_complete=False))
        yield _message(_server_content(text="b", generation_complete=False, turn_complete=True))
        yield _message(_server_content(text=None, generation_complete=True, turn_complete=True))

    llm._session.receive = _receive

    got = []
    async for chunk in llm.send("hi"):
        got.append(chunk)

    assert got == ["a", "b"]


@pytest.mark.asyncio
async def test_send_raises_at_safety_limit():
    with patch("cogency.lib.llms.gemini.get_api_key", return_value="test-key"):
        llm = Gemini()

    llm._session = MagicMock()
    llm._session.send_client_content = AsyncMock()

    async def _receive():
        for _ in range(1001):
            yield _message(None)

    llm._session.receive = _receive

    with pytest.raises(RuntimeError, match="exceeded.*messages"):
        async for _ in llm.send("hi"):
            pass


@pytest.mark.asyncio
async def test_send_enforces_max_session_messages_constant():
    with patch("cogency.lib.llms.gemini.get_api_key", return_value="test-key"):
        llm = Gemini()

    llm._session = MagicMock()
    llm._session.send_client_content = AsyncMock()

    from cogency.lib.llms.gemini import MAX_SESSION_MESSAGES

    async def _receive():
        for _i in range(MAX_SESSION_MESSAGES + 100):
            yield _message(_server_content(text="x"))

    llm._session.receive = _receive

    chunks = []
    with pytest.raises(RuntimeError, match="exceeded.*messages"):
        async for chunk in llm.send("test"):
            chunks.append(chunk)

    assert len(chunks) <= MAX_SESSION_MESSAGES + 1


def test_init_raises_without_api_key():
    with patch("cogency.lib.llms.gemini.get_api_key", return_value=None):
        with pytest.raises(ValueError, match="No API key"):
            Gemini()


def test_init_uses_provided_api_key():
    llm = Gemini(api_key="explicit-key")
    assert llm.api_key == "explicit-key"


@pytest.mark.asyncio
async def test_generate_returns_empty_on_none_text():
    with patch("cogency.lib.llms.gemini.get_api_key", return_value="test-key"):
        llm = Gemini()

    mock_client = MagicMock()
    llm._create_client = MagicMock(return_value=mock_client)
    mock_client.aio.models.generate_content = AsyncMock(return_value=MagicMock(text=None))

    async def _rotation(_prefix, func, *args, **kwargs):
        return await func("test-key")

    with patch("cogency.lib.llms.gemini.with_rotation", _rotation):
        result = await llm.generate([{"role": "user", "content": "hi"}])
    assert result == ""


@pytest.mark.asyncio
async def test_generate_raises_import_error():
    with patch("cogency.lib.llms.gemini.get_api_key", return_value="test-key"):
        llm = Gemini()

    async def _rotation(_prefix, func, *args, **kwargs):
        return await func("test-key")

    with (
        patch("cogency.lib.llms.gemini.with_rotation", _rotation),
        patch.dict("sys.modules", {"google.genai": None}),
        patch.object(llm, "_create_client", side_effect=ImportError("No google.genai")),
    ):
        with pytest.raises(ImportError):
            await llm.generate([{"role": "user", "content": "x"}])


@pytest.mark.asyncio
async def test_stream_yields_text_chunks():
    with patch("cogency.lib.llms.gemini.get_api_key", return_value="test-key"):
        llm = Gemini()

    mock_client = MagicMock()
    llm._create_client = MagicMock(return_value=mock_client)

    async def _stream():
        yield MagicMock(text="a")
        yield MagicMock(text="b")
        yield MagicMock(text=None)
        yield MagicMock(text="c")

    mock_client.aio.models.generate_content_stream = AsyncMock(return_value=_stream())

    async def _rotation(_prefix, func, *args, **kwargs):
        return await func("test-key")

    with patch("cogency.lib.llms.gemini.with_rotation", _rotation):
        chunks = []
        async for chunk in llm.stream([{"role": "user", "content": "hi"}]):
            chunks.append(chunk)
    assert chunks == ["a", "b", "c"]


@pytest.mark.asyncio
async def test_close_noop_for_http_instance():
    with patch("cogency.lib.llms.gemini.get_api_key", return_value="test-key"):
        llm = Gemini()
    await llm.close()


@pytest.mark.asyncio
async def test_close_exits_connection():
    with patch("cogency.lib.llms.gemini.get_api_key", return_value="test-key"):
        llm = Gemini()

    mock_connection = MagicMock()
    mock_connection.__aexit__ = AsyncMock()
    llm._connection = mock_connection
    llm._session = MagicMock()

    await llm.close()

    mock_connection.__aexit__.assert_called_once_with(None, None, None)
    assert llm._session is None
    assert llm._connection is None


@pytest.mark.asyncio
async def test_connect_loads_history_and_drains():
    with patch("cogency.lib.llms.gemini.get_api_key", return_value="test-key"):
        llm = Gemini()

    mock_session = MagicMock()
    mock_session.send_client_content = AsyncMock()

    async def _drain():
        yield _message(_server_content(generation_complete=True, turn_complete=True))

    mock_session.receive = _drain

    mock_connection = MagicMock()
    mock_connection.__aenter__ = AsyncMock(return_value=mock_session)
    mock_connection.__aexit__ = AsyncMock()

    mock_client = MagicMock()
    mock_client.aio.live.connect = MagicMock(return_value=mock_connection)

    async def _rotation(_prefix, func, *args, **kwargs):
        return await func("test-key")

    messages = [
        {"role": "system", "content": "system msg"},
        {"role": "user", "content": "hello"},
        {"role": "assistant", "content": "hi"},
        {"role": "user", "content": "bye"},
    ]

    with (
        patch("cogency.lib.llms.gemini.with_rotation", _rotation),
        patch.object(llm, "_create_client", return_value=mock_client),
    ):
        session = await llm.connect(messages)

    assert session._session is mock_session
    assert session._connection is mock_connection
    assert mock_session.send_client_content.call_count == 2


@pytest.mark.asyncio
async def test_connect_raises_on_setup_failure():
    with patch("cogency.lib.llms.gemini.get_api_key", return_value="test-key"):
        llm = Gemini()

    mock_session = MagicMock()
    mock_session.send_client_content = AsyncMock(side_effect=Exception("setup fail"))

    mock_connection = MagicMock()
    mock_connection.__aenter__ = AsyncMock(return_value=mock_session)
    mock_connection.__aexit__ = AsyncMock()

    mock_client = MagicMock()
    mock_client.aio.live.connect = MagicMock(return_value=mock_connection)

    async def _rotation(_prefix, func, *args, **kwargs):
        return await func("test-key")

    messages = [
        {"role": "user", "content": "u1"},
        {"role": "assistant", "content": "a1"},
        {"role": "user", "content": "u2"},
    ]

    with (
        patch("cogency.lib.llms.gemini.with_rotation", _rotation),
        patch.object(llm, "_create_client", return_value=mock_client),
    ):
        with pytest.raises(RuntimeError, match="connection failed"):
            await llm.connect(messages)

    mock_connection.__aexit__.assert_called_once()


@pytest.mark.asyncio
async def test_send_without_session_raises():
    with patch("cogency.lib.llms.gemini.get_api_key", return_value="test-key"):
        llm = Gemini()

    with pytest.raises(RuntimeError, match="requires active session"):
        async for _ in llm.send("hi"):
            pass


@pytest.mark.asyncio
async def test_drain_exits_at_safety_limit():
    with patch("cogency.lib.llms.gemini.get_api_key", return_value="test-key"):
        llm = Gemini()

    async def _receive():
        for _ in range(MAX_SESSION_MESSAGES + 10):
            yield _message(_server_content(text="x"))

    mock_session = MagicMock()
    mock_session.receive = _receive

    await llm._drain_turn_with_dual_signals(mock_session)


def test_convert_messages_skips_system():
    with patch("cogency.lib.llms.gemini.get_api_key", return_value="test-key"):
        llm = Gemini()

    messages = [
        {"role": "system", "content": "sys"},
        {"role": "user", "content": "u"},
        {"role": "assistant", "content": "a"},
    ]
    result = llm._convert_messages_to_gemini_format(messages)
    assert len(result) == 2
