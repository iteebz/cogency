import asyncio
import contextlib
from unittest.mock import AsyncMock, patch

import pytest

from cogency.context import profile
from cogency.lib.sqlite import SQLite


@pytest.mark.asyncio
async def test_get():
    assert await profile.get(None) is None


@pytest.mark.asyncio
async def test_format():
    with patch("cogency.context.profile.get", return_value={}):
        result = await profile.format("user123")
        assert result == ""


@pytest.mark.asyncio
async def test_should_learn(mock_config, tmp_path):
    # No profile = no learning
    with patch("cogency.context.profile.get", return_value=None):
        assert not await profile.should_learn(
            "user1",
            storage=mock_config.storage,
        )

    # Mock profile exists
    mock_profile = {"who": "Alice", "_meta": {"last_learned_at": 100}}

    with patch("cogency.context.profile.get", return_value=mock_profile):
        # Add messages to storage to trigger learning
        for i in range(5):
            await mock_config.storage.save_message(
                "conv1", "user1", "user", f"message {i}", timestamp=110 + i
            )

        result = await profile.should_learn(
            "user1",
            storage=mock_config.storage,
        )
        assert result


@pytest.mark.asyncio
async def test_learn_async(mock_config, tmp_path):
    # Mock LLM response
    mock_config.llm.generate.return_value = (
        '{"who": "Alice", "interests": "programming", "style": "direct"}'
    )

    # Set up existing profile
    mock_profile = {"who": "Bob", "_meta": {"last_learned_at": 100}}

    storage = SQLite(db_path=f"{tmp_path}/test.db")
    await storage.save_message("conv1", "user1", "user", "I love coding Python", 110)
    await storage.save_message("conv1", "user1", "user", "Can you help with algorithms?", 120)

    # Update config to use temporary storage
    mock_config.storage = storage

    with (
        patch("cogency.context.profile.get", return_value=mock_profile),
        patch(
            "cogency.context.profile._should_learn_with_profile",
            new_callable=AsyncMock,
            return_value=True,
        ),
    ):
        mock_save = AsyncMock()
        storage.save_profile = mock_save

        result = await profile.learn_async(
            "user1",
            storage=mock_config.storage,
            llm=mock_config.llm,
        )

        assert result is True
        mock_config.llm.generate.assert_called_once()
        mock_save.assert_called_once()

        # Check learning prompt contained user messages
        call_args = mock_config.llm.generate.call_args[0][0]
        prompt_text = str(call_args)
        assert "I love coding Python" in prompt_text
        assert "Can you help with algorithms?" in prompt_text


def test_learn_disabled(mock_config):
    result = profile.learn(
        "user123",
        profile_enabled=False,
        storage=mock_config.storage,
        llm=mock_config.llm,
    )
    assert result is None


def test_prompt_compact():
    current = {"who": "Alice", "style": "verbose"}
    messages = ["hello", "world"]
    result = profile.prompt(current, messages, compact=True)
    assert "Compact to essential facts" in result
    assert "hello" in result


@pytest.mark.asyncio
async def test_get_database_error():
    mock_storage = AsyncMock()
    mock_storage.load_profile.side_effect = Exception("unable to open database file")
    result = await profile.get("user1", mock_storage)
    assert result == {}


@pytest.mark.asyncio
async def test_get_other_error_raises():
    mock_storage = AsyncMock()
    mock_storage.load_profile.side_effect = Exception("network failure")
    with pytest.raises(RuntimeError, match="Profile fetch failed"):
        await profile.get("user1", mock_storage)


@pytest.mark.asyncio
async def test_format_with_profile():
    mock_storage = AsyncMock()
    mock_storage.load_profile.return_value = {"who": "Bob"}
    result = await profile.format("user1", mock_storage)
    assert "USER PROFILE" in result
    assert "Bob" in result


@pytest.mark.asyncio
async def test_format_error_raises():
    with patch("cogency.context.profile.get", side_effect=Exception("boom")):
        with pytest.raises(RuntimeError, match="Profile format failed"):
            await profile.format("user1")


@pytest.mark.asyncio
async def test_should_learn_initial_learning():
    mock_storage = AsyncMock()
    mock_storage.count_user_messages.return_value = 5
    with patch("cogency.context.profile.get", return_value=None):
        result = await profile.should_learn("user1", storage=mock_storage)
        assert result is True


@pytest.mark.asyncio
async def test_should_learn_compact_trigger():
    large_profile = {"who": "x" * 2500, "_meta": {"last_learned_at": 100}}
    mock_storage = AsyncMock()
    with patch("cogency.context.profile.get", return_value=large_profile):
        result = await profile.should_learn("user1", storage=mock_storage)
        assert result is True


@pytest.mark.asyncio
async def test_should_learn_returns_false_below_cadence():
    mock_profile = {"who": "Alice", "_meta": {"last_learned_at": 100}}
    mock_storage = AsyncMock()
    mock_storage.count_user_messages.return_value = 2
    with patch("cogency.context.profile.get", return_value=mock_profile):
        result = await profile.should_learn("user1", storage=mock_storage)
        assert result is False


def test_task_done_callback_cancelled():
    task = AsyncMock(spec=asyncio.Task)
    task.cancelled.return_value = True
    profile._background_tasks.add(task)
    profile._task_done_callback(task)
    assert task not in profile._background_tasks


def test_task_done_callback_exception():
    task = AsyncMock(spec=asyncio.Task)
    task.cancelled.return_value = False
    task.exception.return_value = Exception("test error")
    profile._background_tasks.add(task)
    profile._task_done_callback(task)
    assert task not in profile._background_tasks


@pytest.mark.asyncio
async def test_wait_for_background_tasks_empty():
    profile._background_tasks.clear()
    await profile.wait_for_background_tasks()


@pytest.mark.asyncio
async def test_wait_for_background_tasks_timeout():
    async def slow_task():
        await asyncio.sleep(100)

    loop = asyncio.get_event_loop()
    task = loop.create_task(slow_task())
    profile._background_tasks.add(task)
    try:
        await profile.wait_for_background_tasks(timeout=0.01)
    finally:
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task
        profile._background_tasks.discard(task)


@pytest.mark.asyncio
async def test_learn_async_no_messages():
    mock_storage = AsyncMock()
    mock_storage.load_user_messages.return_value = []
    mock_llm = AsyncMock()
    with (
        patch("cogency.context.profile.get", return_value={"_meta": {"last_learned_at": 0}}),
        patch("cogency.context.profile._should_learn_with_profile", return_value=True),
    ):
        result = await profile.learn_async("user1", storage=mock_storage, llm=mock_llm)
        assert result is False


@pytest.mark.asyncio
async def test_learn_async_no_update_needed():
    mock_storage = AsyncMock()
    mock_storage.load_user_messages.return_value = ["hello"]
    mock_llm = AsyncMock()
    mock_llm.generate.return_value = "{}"
    with (
        patch(
            "cogency.context.profile.get",
            return_value={"who": "Alice", "_meta": {"last_learned_at": 0}},
        ),
        patch("cogency.context.profile._should_learn_with_profile", return_value=True),
    ):
        result = await profile.learn_async("user1", storage=mock_storage, llm=mock_llm)
        assert result is False


@pytest.mark.asyncio
async def test_update_profile_compact_fallback():
    mock_llm = AsyncMock()
    mock_llm.generate.return_value = ""
    current = {"who": "Alice"}
    result = await profile.update_profile(current, ["msg"], mock_llm, compact=True)
    assert result == current


@pytest.mark.asyncio
async def test_update_profile_json_error():
    mock_llm = AsyncMock()
    mock_llm.generate.return_value = "not valid json"
    with pytest.raises(RuntimeError, match="JSON parse error"):
        await profile.update_profile({}, ["msg"], mock_llm)


@pytest.mark.asyncio
async def test_update_profile_invalid_format():
    mock_llm = AsyncMock()
    mock_llm.generate.return_value = '["array", "not", "dict"]'
    with pytest.raises(RuntimeError, match="Invalid profile format"):
        await profile.update_profile({}, ["msg"], mock_llm)


@pytest.mark.asyncio
async def test_learn_async_should_learn_false():
    mock_storage = AsyncMock()
    mock_llm = AsyncMock()
    with (
        patch("cogency.context.profile.get", return_value={"who": "Alice", "_meta": {}}),
        patch("cogency.context.profile._should_learn_with_profile", return_value=False),
    ):
        result = await profile.learn_async("user1", storage=mock_storage, llm=mock_llm)
        assert result is False


@pytest.mark.asyncio
async def test_learn_spawns_background_task(mock_config):
    profile._background_tasks.clear()
    with patch("cogency.context.profile.learn_async", new_callable=AsyncMock) as mock_learn:
        mock_learn.return_value = True
        profile.learn(
            "user123",
            profile_enabled=True,
            storage=mock_config.storage,
            llm=mock_config.llm,
        )
        await asyncio.sleep(0.01)
        mock_learn.assert_called_once()
    profile._background_tasks.clear()
