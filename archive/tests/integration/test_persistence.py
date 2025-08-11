"""Simple integration test for state persistence functionality."""

import tempfile
from unittest.mock import patch

import pytest

from cogency import Agent
from cogency.config import PersistConfig
from cogency.storage.state import SQLite


@pytest.mark.asyncio
async def test_agent_setup():
    """Test that Agent properly sets up persistence components."""

    with tempfile.TemporaryDirectory() as temp_dir:
        store = SQLite(f"{temp_dir}/test.db")

        # Test persistence enabled
        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
            persist_config = PersistConfig(enabled=True, store=store)
            agent = Agent("test_agent", tools=[], persist=persist_config)
            # Agent now sets up components directly in __init__, no _get_executor needed
            assert agent.llm is not None

        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
            agent = Agent("test_agent", tools=[])
            # Agent now sets up components directly in __init__
            assert agent.llm is not None
