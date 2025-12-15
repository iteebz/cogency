from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from cogency.lib.llms import Gemini


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
async def test_send_stops_at_safety_limit():
    with patch("cogency.lib.llms.gemini.get_api_key", return_value="test-key"):
        llm = Gemini()

    llm._session = MagicMock()
    llm._session.send_client_content = AsyncMock()

    async def _receive():
        for _ in range(1001):
            yield _message(None)

    llm._session.receive = _receive

    got = []
    async for chunk in llm.send("hi"):
        got.append(chunk)

    assert got == []


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
    async for chunk in llm.send("test"):
        chunks.append(chunk)

    assert MAX_SESSION_MESSAGES < len(chunks) < MAX_SESSION_MESSAGES + 5
