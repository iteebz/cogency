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
