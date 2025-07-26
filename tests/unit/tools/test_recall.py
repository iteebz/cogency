"""Recall tool tests."""

from unittest.mock import AsyncMock, Mock

import pytest

from cogency.tools.recall import Recall


@pytest.mark.asyncio
async def test_interface():
    mock_memory = Mock()
    recall_tool = Recall(memory=mock_memory)

    assert recall_tool.name == "recall"
    assert recall_tool.description
    assert hasattr(recall_tool, "run")

    schema = recall_tool.schema
    examples = recall_tool.examples
    assert isinstance(schema, str) and len(schema) > 0
    assert isinstance(examples, list) and len(examples) > 0


@pytest.mark.asyncio
async def test_basic_recall():
    mock_memory = AsyncMock()
    mock_memory.search_similarity = AsyncMock(return_value=[])
    recall_tool = Recall(memory=mock_memory)

    result = await recall_tool.run(query="test")
    assert result.success
    assert result.data["query"] == "test"
