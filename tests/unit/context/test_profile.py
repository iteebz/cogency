"""Profile tests."""

import tempfile
from unittest.mock import AsyncMock, Mock, patch

import pytest

from cogency.context import profile
from cogency.lib.storage import save_message


@pytest.mark.asyncio
async def test_get():
    """Get returns None for None/default user_ids."""
    assert await profile.get(None) is None
    assert await profile.get("default") is None


@pytest.mark.asyncio
async def test_format():
    """Format returns empty string for empty profile."""
    with patch("cogency.context.profile.get", return_value={}):
        result = await profile.format("user123")
        assert result == ""


@pytest.mark.asyncio
async def test_should_learn_logic():
    """Should learn triggers on message count and compression threshold."""

    with tempfile.TemporaryDirectory() as temp_dir:
        # No profile = no learning
        with patch("cogency.context.profile.get", return_value=None):
            assert not await profile.should_learn("user1")

        # Mock profile exists
        mock_profile = {"who": "Alice", "_meta": {"last_learned_at": 100}}

        with patch("cogency.context.profile.get", return_value=mock_profile):
            # Save some user messages after timestamp 100
            await save_message("conv1", "user1", "user", "Message 1", temp_dir, 110)
            await save_message("conv1", "user1", "user", "Message 2", temp_dir, 120)
            await save_message("conv1", "user1", "user", "Message 3", temp_dir, 130)
            await save_message("conv1", "user1", "user", "Message 4", temp_dir, 140)
            await save_message("conv1", "user1", "user", "Message 5", temp_dir, 150)

            from pathlib import Path

            with patch("cogency.lib.storage.Paths.db", return_value=Path(temp_dir) / "store.db"):
                # 5+ messages should trigger learning
                assert await profile.should_learn("user1")


@pytest.mark.asyncio
async def test_learn_async_logic():
    """Learn async generates profile from messages."""

    with tempfile.TemporaryDirectory() as temp_dir:
        # Mock LLM that returns learning result
        mock_llm = Mock()
        mock_llm.generate = AsyncMock(
            return_value='{"who": "Alice", "interests": "programming", "style": "direct"}'
        )

        # Set up existing profile
        mock_profile = {"who": "Bob", "_meta": {"last_learned_at": 100}}

        # Add user messages
        await save_message("conv1", "user1", "user", "I love coding Python", temp_dir, 110)
        await save_message("conv1", "user1", "user", "Can you help with algorithms?", temp_dir, 120)

        with patch("cogency.context.profile.get", return_value=mock_profile):
            with patch(
                "cogency.context.profile.should_learn", new_callable=AsyncMock, return_value=True
            ):
                from pathlib import Path

                with patch(
                    "cogency.lib.storage.Paths.db", return_value=Path(temp_dir) / "store.db"
                ):
                    with patch(
                        "cogency.context.profile.save_profile",
                        new_callable=AsyncMock,
                        return_value=True,
                    ) as mock_save:
                        # Should learn and update profile
                        result = await profile.learn_async("user1", mock_llm)

                        assert result is True
                        mock_llm.generate.assert_called_once()
                        mock_save.assert_called_once()

                        # Check learning prompt contained user messages
                        call_args = mock_llm.generate.call_args[0][0]
                        prompt_text = str(call_args)
                        assert "I love coding Python" in prompt_text
                        assert "Can you help with algorithms?" in prompt_text


def test_learn_pytest_detection():
    """Learn detects pytest environment and returns early."""
    mock_llm = Mock()

    # This should return None due to pytest detection
    result = profile.learn("user123", mock_llm)
    assert result is None
