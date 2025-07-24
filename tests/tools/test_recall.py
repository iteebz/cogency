"""Test Recall tool business logic."""

from unittest.mock import AsyncMock, Mock

import pytest

from cogency.tools.recall import Recall


class TestRecall:
    """Test Recall tool business logic."""

    @pytest.mark.asyncio
    async def test_interface(self):
        """Recall tool implements required interface."""
        mock_memory = Mock()
        recall_tool = Recall(memory=mock_memory)

        # Required attributes
        assert recall_tool.name == "recall"
        assert recall_tool.description
        assert hasattr(recall_tool, "run")

        # Schema and examples
        schema = recall_tool.schema
        examples = recall_tool.examples
        assert isinstance(schema, str) and len(schema) > 0
        assert isinstance(examples, list) and len(examples) > 0

    @pytest.mark.asyncio
    async def test_empty_query(self):
        """Recall tool handles empty query."""
        mock_memory = Mock()
        recall_tool = Recall(memory=mock_memory)

        result = await recall_tool.run(query="")
        assert not result.success
        assert "query parameter is required" in result.error

    @pytest.mark.asyncio
    async def test_basic_recall(self):
        """Recall tool can perform basic memory recall."""
        mock_memory = AsyncMock()
        mock_memory.search_similarity = AsyncMock(return_value=[])
        recall_tool = Recall(memory=mock_memory)

        # Use a simple query
        result = await recall_tool.run(query="test")
        # Should call memory.search_similarity
        assert result.success
        assert result.data["query"] == "test"
