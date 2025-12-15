"""Storage error contract for context assembly.

Spec: Context is rebuilt from storage on every execution.
Contract: Storage errors must propagate, not be silently swallowed.
Rationale: The stateless rebuild architecture depends on storage as source of truth.
Silent failure violates this contract and corrupts agent state.

Error layers:
- Message load errors → critical (history unavailable)
- Profile format errors → critical (preferences unavailable, but non-blocking)
- Empty results → valid (new conversation)
"""

import pytest

from cogency.context.assembly import assemble


@pytest.mark.asyncio
async def test_message_load_error_propagates():
    """Conversation history load failure must raise."""

    class CorruptedStorage:
        async def save_message(self, *args, **kwargs):
            raise NotImplementedError

        async def load_messages(self, conv_id, user_id, limit=None):
            raise RuntimeError("Database corrupted: checksum mismatch")

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

    with pytest.raises(RuntimeError, match="corrupted"):
        await assemble(
            user_id="user",
            conversation_id="conv",
            tools=[],
            storage=CorruptedStorage(),  # type: ignore[arg-type]
            history_window=None,
            history_transform=None,
            profile_enabled=False,
        )


@pytest.mark.asyncio
async def test_message_load_empty_succeeds():
    """Empty message history is valid (new conversation)."""

    class EmptyStorage:
        async def save_message(self, *args, **kwargs):
            raise NotImplementedError

        async def load_messages(self, conv_id, user_id, limit=None):
            return []

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

    result = await assemble(
        user_id="user",
        conversation_id="conv",
        tools=[],
        storage=EmptyStorage(),  # type: ignore[arg-type]
        history_window=None,
        history_transform=None,
        profile_enabled=False,
    )

    assert isinstance(result, list)
    assert len(result) >= 1
    assert result[0]["role"] == "system"


@pytest.mark.asyncio
async def test_profile_error_propagates_when_enabled():
    """Profile loading errors must raise when profile_enabled=True."""

    class NoProfileStorage:
        async def save_message(self, *args, **kwargs):
            raise NotImplementedError

        async def load_messages(self, conv_id, user_id, limit=None):
            return []

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

    async def broken_profile_format(user_id, storage):
        raise RuntimeError("Profile store unavailable")

    import cogency.context.assembly as assembly_module

    original = assembly_module.profile_format
    assembly_module.profile_format = broken_profile_format

    try:
        with pytest.raises(RuntimeError, match="unavailable"):
            await assemble(
                user_id="user",
                conversation_id="conv",
                tools=[],
                storage=NoProfileStorage(),  # type: ignore[arg-type]
                history_window=None,
                history_transform=None,
                profile_enabled=True,
            )
    finally:
        assembly_module.profile_format = original


@pytest.mark.asyncio
async def test_profile_disabled_skips_load():
    """Profile loading skipped when profile_enabled=False."""

    class BrokenProfileStorage:
        async def save_message(self, *args, **kwargs):
            raise NotImplementedError

        async def load_messages(self, conv_id, user_id, limit=None):
            return []

        async def save_event(self, *args, **kwargs):
            raise NotImplementedError

        async def save_request(self, *args, **kwargs):
            raise NotImplementedError

        async def save_profile(self, *args, **kwargs):
            raise NotImplementedError

        async def load_profile(self, user_id):
            raise RuntimeError("Profile store down")

        async def count_user_messages(self, *args, **kwargs):
            return 0

        async def load_user_messages(self, *args, **kwargs):
            return []

    # Should not raise - profile loading skipped
    result = await assemble(
        user_id="user",
        conversation_id="conv",
        tools=[],
        storage=BrokenProfileStorage(),  # type: ignore[arg-type]
        history_window=None,
        history_transform=None,
        profile_enabled=False,
    )

    assert result[0]["role"] == "system"
