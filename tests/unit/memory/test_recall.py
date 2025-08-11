"""Unit tests for RecallTool."""

from unittest.mock import AsyncMock, patch

import pytest

from cogency.tools.recall import Recall


@pytest.fixture
def mock_archival():
    archival = AsyncMock()
    archival.search_topics.return_value = [
        {
            "topic": "Python",
            "content": "List comprehensions are faster than for loops",
            "similarity": 0.85,
            "updated": "2024-01-01T00:00:00",
        }
    ]
    return archival


@pytest.fixture
def recall_tool(mock_archival):
    return Recall()


@pytest.mark.asyncio
@patch("cogency.memory.archive.archive")
async def test_successful_recall(mock_archive):
    # Mock the async method properly
    mock_archive.search_topics = AsyncMock(
        return_value=[
            {
                "content": "Python performance optimization techniques",
                "topic": "Python Performance",
                "updated": "2024-01-01T00:00:00",
                "similarity": 0.85,
            }
        ]
    )

    tool = Recall()
    result = await tool.run(query="python performance", user_id="user1")

    assert result.success
    assert result.data["count"] == 1
    assert "Python" in result.data["response"]
    mock_archive.search_topics.assert_called_once_with(
        user_id="user1", query="python performance", limit=3, min_similarity=0.7
    )


@pytest.mark.asyncio
@patch("cogency.memory.archive.archive")
async def test_no_results_found(mock_archive):
    # Mock the async method properly
    mock_archive.search_topics = AsyncMock(return_value=[])

    tool = Recall()
    result = await tool.run(query="nonexistent topic", user_id="user1")

    assert result.success
    assert result.data["count"] == 0
    assert "No relevant knowledge found" in result.data["response"]


def test_single_topic(recall_tool):
    results = [{"topic": "Python", "content": "List comprehensions are fast", "similarity": 0.85}]

    formatted = recall_tool._format_results(results, "test query")

    assert "1. Python" in formatted
    assert "List comprehensions are fast" in formatted
    assert "similarity: 0.85" in formatted


def test_multiple_topics(recall_tool):
    results = [
        {"topic": "Python", "content": "Fast code", "similarity": 0.9},
        {"topic": "JavaScript", "content": "Async patterns", "similarity": 0.8},
    ]

    formatted = recall_tool._format_results(results, "test query")

    assert "1. Python" in formatted
    assert "2. JavaScript" in formatted
    assert formatted.count("similarity:") == 2
