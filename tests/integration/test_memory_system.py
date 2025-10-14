from unittest.mock import patch

import pytest

from cogency.context import profile
from cogency.lib.sqlite import SQLite


@pytest.mark.asyncio
async def test_integration(mock_llm, tmp_path):
    storage = SQLite(db_path=f"{tmp_path}/test.db")
    mock_llm.generate.return_value = (
        '{"who": "Alice", "interests": "programming", "style": "concise"}'
    )

    mock_profile = {"who": "Bob", "_meta": {"last_learned_at": 100}}
    with patch("cogency.context.profile.get", return_value=mock_profile):
        await storage.save_message("conv1", "user1", "user", "I love Python", 110)
        await storage.save_message("conv1", "user1", "user", "Help me with async", 120)
        await storage.save_message("conv1", "user1", "user", "Third message", 130)
        await storage.save_message("conv1", "user1", "user", "Fourth message", 140)
        await storage.save_message("conv1", "user1", "user", "Fifth message", 150)

        should_learn = await profile.should_learn("user1", storage=storage)
        assert should_learn

        learned = await profile.learn_async("user1", storage=storage, llm=mock_llm)
        assert learned is True
        mock_llm.generate.assert_called_once()
