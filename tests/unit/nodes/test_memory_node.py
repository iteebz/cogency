import pytest
from unittest.mock import AsyncMock, Mock

from cogency.nodes.memory import memorize
from cogency.common.types import AgentState

class TestMemoryNode:
    @pytest.fixture
    def mock_agent_state(self):
        return AgentState(query="test query", response="", intermediate_steps=[])

    @pytest.mark.asyncio
    async def test_memorize_should_store_true(self, mock_agent_state):
        mock_memory = Mock()
        mock_memory.should_store.return_value = (True, "test_category")
        mock_memory.memorize = AsyncMock()

        result_state = await memorize(mock_agent_state, memory=mock_memory)

        mock_memory.should_store.assert_called_once_with("test query")
        mock_memory.memorize.assert_called_once_with("test query", tags=["test_category"])
        assert result_state == mock_agent_state

    @pytest.mark.asyncio
    async def test_memorize_should_store_false(self, mock_agent_state):
        mock_memory = Mock()
        mock_memory.should_store.return_value = (False, "test_category")
        mock_memory.memorize = AsyncMock()

        result_state = await memorize(mock_agent_state, memory=mock_memory)

        mock_memory.should_store.assert_called_once_with("test query")
        mock_memory.memorize.assert_not_called()
        assert result_state == mock_agent_state

    @pytest.mark.asyncio
    async def test_memorize_no_should_store_method(self, mock_agent_state):
        mock_memory = Mock()
        # Ensure should_store method is not present
        del mock_memory.should_store
        mock_memory.memorize = AsyncMock()

        result_state = await memorize(mock_agent_state, memory=mock_memory)

        mock_memory.memorize.assert_not_called()
        assert result_state == mock_agent_state
