"""Context assembly tests - stateless context rebuilding."""

import pytest

from cogency import context


@pytest.mark.asyncio
async def test_assembly(mock_config):
    """Assembly produces system + user messages with correct content."""
    query = "Test query"
    messages = await context.assemble(query, "user_123", "conv_123", config=mock_config)

    # System message first
    assert messages[0]["role"] == "system"
    assert len(messages[0]["content"]) > 0

    # User message last with exact query
    assert messages[-1]["role"] == "user"
    assert messages[-1]["content"] == query

    assert len(messages) >= 2
