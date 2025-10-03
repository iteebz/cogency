import pytest

from cogency import context


@pytest.mark.asyncio
async def test_assembly(mock_config):
    messages = await context.assemble(
        "user_123",
        "conv_123",
        tools=mock_config.tools,
        storage=mock_config.storage,
        history_window=mock_config.history_window,
        profile_enabled=mock_config.profile,
    )

    # System message first
    assert messages[0]["role"] == "system"
    assert len(messages[0]["content"]) > 0

    # User message is ephemeral "continue" trigger
    assert messages[-1]["role"] == "user"
    assert messages[-1]["content"] == "continue"

    assert len(messages) >= 2
