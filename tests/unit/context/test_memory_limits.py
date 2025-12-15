"""Memory limit enforcement tests."""

import pytest

from cogency.context.assembly import MAX_CONVERSATION_LENGTH, assemble
from cogency.core.errors import StorageError


@pytest.mark.asyncio
async def test_conversation_length_limit_enforced():
    """Context assembly rejects unbounded conversations exceeding MAX_CONVERSATION_LENGTH."""

    class OversizedStorage:
        async def load_messages(self, conv_id, user_id, limit=None):
            # Simulate conversation with events exceeding limit
            return [
                {"type": "user", "content": f"msg_{i}", "timestamp": float(i)}
                for i in range(MAX_CONVERSATION_LENGTH + 1)
            ]

        async def save_message(self, *args, **kwargs):
            raise NotImplementedError

        async def save_event(self, *args, **kwargs):
            raise NotImplementedError

        async def save_request(self, *args, **kwargs):
            raise NotImplementedError

        async def save_profile(self, *args, **kwargs):
            raise NotImplementedError

        async def load_profile(self, *args, **kwargs):
            return {}

        async def count_user_messages(self, *args, **kwargs):
            return 0

        async def load_user_messages(self, *args, **kwargs):
            return []

    with pytest.raises(StorageError, match="exceeds.*Enable history_window"):
        await assemble(
            user_id="user",
            conversation_id="conv",
            tools=[],
            storage=OversizedStorage(),  # type: ignore[arg-type]
            history_window=None,
            history_transform=None,
            profile_enabled=False,
        )


@pytest.mark.asyncio
async def test_conversation_length_limit_bypassed_with_window():
    """history_window bypasses length check - database loads bounded set."""

    class OversizedStorage:
        async def load_messages(self, conv_id, user_id, limit=None):
            # With history_window, limit is set, so return bounded results
            if limit:
                return [
                    {"type": "user", "content": f"msg_{i}", "timestamp": float(i)}
                    for i in range(min(limit, 100))
                ]
            # Without window, would exceed limit
            return [
                {"type": "user", "content": f"msg_{i}", "timestamp": float(i)}
                for i in range(MAX_CONVERSATION_LENGTH + 1)
            ]

        async def save_message(self, *args, **kwargs):
            raise NotImplementedError

        async def save_event(self, *args, **kwargs):
            raise NotImplementedError

        async def save_request(self, *args, **kwargs):
            raise NotImplementedError

        async def save_profile(self, *args, **kwargs):
            raise NotImplementedError

        async def load_profile(self, *args, **kwargs):
            return {}

        async def count_user_messages(self, *args, **kwargs):
            return 0

        async def load_user_messages(self, *args, **kwargs):
            return []

    # Should succeed - history_window limits load
    messages = await assemble(
        user_id="user",
        conversation_id="conv",
        tools=[],
        storage=OversizedStorage(),  # type: ignore[arg-type]
        history_window=20,
        history_transform=None,
        profile_enabled=False,
    )

    assert len(messages) >= 1
    assert messages[0]["role"] == "system"


@pytest.mark.asyncio
async def test_conversation_at_limit_succeeds():
    """Conversations exactly at MAX_CONVERSATION_LENGTH are allowed."""

    class AtLimitStorage:
        async def load_messages(self, conv_id, user_id, limit=None):
            return [
                {"type": "user", "content": f"msg_{i}", "timestamp": float(i)}
                for i in range(MAX_CONVERSATION_LENGTH)
            ]

        async def save_message(self, *args, **kwargs):
            raise NotImplementedError

        async def save_event(self, *args, **kwargs):
            raise NotImplementedError

        async def save_request(self, *args, **kwargs):
            raise NotImplementedError

        async def save_profile(self, *args, **kwargs):
            raise NotImplementedError

        async def load_profile(self, *args, **kwargs):
            return {}

        async def count_user_messages(self, *args, **kwargs):
            return 0

        async def load_user_messages(self, *args, **kwargs):
            return []

    messages = await assemble(
        user_id="user",
        conversation_id="conv",
        tools=[],
        storage=AtLimitStorage(),  # type: ignore[arg-type]
        history_window=None,
        history_transform=None,
        profile_enabled=False,
    )

    assert len(messages) >= 1
