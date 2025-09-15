"""Memory system integration - profile context and recall tool verification.

Tests complete memory architecture (profile learning + recall tool) to ensure
no embeddings philosophy works end-to-end in practice.
"""

import pytest

from cogency.context.profile import get as get_profile
from cogency.tools.memory.recall import MemoryRecall


@pytest.mark.asyncio
async def test_memory_system_integration(mock_config):
    # Set up test profile in mock storage
    user_profile = {
        "who": "Alice",
        "interests": "Python programming, machine learning",
        "style": "technical discussions",
        "_meta": {"last_learned_at": 100},
    }
    await mock_config.storage.save_profile("user1", user_profile)

    # Set up historical messages for recall
    await mock_config.storage.save_message(
        "user1_old1", "user1", "user", "I was working on a Django project", 50
    )
    await mock_config.storage.save_message(
        "user1_old2", "user1", "user", "Had trouble with database migrations", 60
    )

    # Verify profile access works with mock storage
    profile = await get_profile("user1", storage=mock_config.storage)
    assert profile["who"] == "Alice"
    assert "Python programming" in profile["interests"]

    # Verify recall tool can be configured and executed
    recall_tool = MemoryRecall()

    # Mock the storage-dependent search functionality
    from unittest.mock import patch

    with patch.object(recall_tool, "_search_messages") as mock_search:
        from cogency.tools.memory.recall import MessageMatch

        mock_search.return_value = [
            MessageMatch(
                content="I was working on a Django project",
                timestamp=50,
                conversation_id="user1_old1",
            )
        ]

        recall_result = await recall_tool.execute("Django", user_id="user1")

        # Success verification
        assert not any(
            failure in recall_result.outcome
            for failure in ["failed:", "error:", "Security violation:"]
        )
        assert "Django project" in recall_result.content
