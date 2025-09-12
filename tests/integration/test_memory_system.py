"""Memory system integration test - profile + recall working together."""

import tempfile
from unittest.mock import Mock, patch

import pytest

from cogency import Agent
from cogency.lib.storage import SQLite, save_message, save_profile


@pytest.mark.asyncio
async def test_memory_system_integration():
    """Memory system provides both profile context and recall capability."""

    with tempfile.TemporaryDirectory() as temp_dir:
        # Set up user profile
        user_profile = {
            "who": "Alice",
            "interests": "Python programming, machine learning",
            "style": "technical discussions",
            "_meta": {"last_learned_at": 100},
        }
        save_profile("user1", user_profile, temp_dir)

        # Set up historical messages for recall (must use user1_ prefix)
        save_message(
            "user1_old1", "user1", "user", "I was working on a Django project", temp_dir, 50
        )
        save_message(
            "user1_old2", "user1", "user", "Had trouble with database migrations", temp_dir, 60
        )
        save_message("user1_old3", "user1", "user", "Finally got the API working", temp_dir, 70)

        # Mock LLM with simple response
        mock_llm = Mock()

        async def mock_stream(messages):
            yield "§RESPOND\n"
            yield "I understand you're asking about your past work.\n"
            yield "§END\n"

        mock_llm.stream = mock_stream

        from pathlib import Path

        with patch("cogency.lib.storage.Paths.db", return_value=Path(temp_dir) / "store.db"):
            with patch("cogency.lib.llms.Gemini", return_value=mock_llm):
                storage = SQLite(temp_dir)
                agent = Agent(llm="gemini", storage=storage, profile=True, mode="replay")

                # Verify agent can access profile
                from cogency.context.profile import get

                profile = get("user1")
                assert profile["who"] == "Alice"
                assert "Python programming" in profile["interests"]

                # Verify recall tool can find messages
                from cogency.tools.memory.recall import MemoryRecall

                recall_tool = MemoryRecall()
                recall_result = await recall_tool.execute("Django", user_id="user1")
                assert recall_result.success
                assert "Django project" in recall_result.unwrap().content

                # Verify agent has recall tool available
                tool_names = {tool.name for tool in agent.config.tools}
                assert "recall" in tool_names

                # Verify basic agent functionality still works
                responses = []
                async for event in agent("Tell me about my past work", user_id="user1"):
                    if event["type"] == "respond":
                        responses.append(event["content"])

                response = "".join(responses)
                assert isinstance(response, str)
                assert len(response) > 0
