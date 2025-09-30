import tempfile
from unittest.mock import patch

import pytest

from cogency.context import profile
from cogency.lib.storage import SQLite


@pytest.mark.asyncio
async def test_memory_system_integration(mock_llm):
    with tempfile.TemporaryDirectory() as temp_dir:
        storage = SQLite(temp_dir)

        mock_llm.generate.return_value = '{"who": "Alice", "interests": "programming", "style": "concise"}'

        mock_profile = {"who": "Bob", "_meta": {"last_learned_at": 100}}
        with patch("cogency.context.profile.get", return_value=mock_profile):
            await storage.save_message("conv1", "user1", "user", "I love Python", 110)
            await storage.save_message("conv1", "user1", "user", "Help me with async", 120)
            await storage.save_message("conv1", "user1", "user", "Third message", 130)
            await storage.save_message("conv1", "user1", "user", "Fourth message", 140)
            await storage.save_message("conv1", "user1", "user", "Fifth message", 150)

            should_learn = await profile.should_learn("user1", storage=storage, learn_every=5)
            assert should_learn

            learned = await profile.learn_async("user1", storage=storage, learn_every=5, llm=mock_llm)
            assert learned is True
            mock_llm.generate.assert_called_once()