"""Context assembly tests."""

import pytest

from cogency.context import context


@pytest.mark.asyncio
async def test_assembly():
    """Assembly produces system + user messages with correct content."""
    query = "Test query"
    messages = await context.assemble(query, "user_123", "conv_123", config=None)

    # System message first
    assert messages[0]["role"] == "system"
    assert len(messages[0]["content"]) > 0

    # User message last with exact query
    assert messages[-1]["role"] == "user"
    assert messages[-1]["content"] == query

    assert len(messages) >= 2
