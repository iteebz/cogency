"""Unit tests for RecallTool."""

import pytest
from unittest.mock import AsyncMock, Mock
from resilient_result import Ok, Err

from cogency.tools.recall import Recall


class TestRecall:
    @pytest.fixture
    def mock_archival(self):
        archival = AsyncMock()
        archival.search_topics.return_value = [
            {
                "topic": "Python",
                "content": "List comprehensions are faster than for loops",
                "similarity": 0.85,
                "updated": "2024-01-01T00:00:00"
            }
        ]
        return archival

    @pytest.fixture
    def recall_tool(self, mock_archival):
        tool = Recall(mock_archival)
        tool.set_context("user1", mock_archival)
        return tool

    @pytest.mark.asyncio
    async def test_successful_recall(self, recall_tool, mock_archival):
        result = await recall_tool.run(query="python performance", min_similarity=0.7)
        
        assert result.success
        assert result.data["count"] == 1
        assert "Python" in result.data["response"]
        mock_archival.search_topics.assert_called_once_with(
            "user1", "python performance", limit=3, min_similarity=0.7
        )

    @pytest.mark.asyncio
    async def test_no_results_found(self, recall_tool, mock_archival):
        mock_archival.search_topics.return_value = []
        
        result = await recall_tool.run(query="nonexistent topic")
        
        assert result.success
        assert result.data["count"] == 0
        assert "No relevant memories found" in result.data["response"]

    @pytest.mark.asyncio
    async def test_missing_context(self):
        tool = Recall(AsyncMock())
        # Don't set context
        
        result = await tool.run(query="test")
        
        assert not result.success
        assert "Context not set" in str(result.error)

    def test_format_results_single_topic(self, recall_tool):
        results = [
            {
                "topic": "Python",
                "content": "List comprehensions are fast",
                "similarity": 0.85
            }
        ]
        
        formatted = recall_tool._format_results(results)
        
        assert "## Python" in formatted
        assert "List comprehensions are fast" in formatted
        assert "Similarity: 85%" in formatted

    def test_format_results_multiple_topics(self, recall_tool):
        results = [
            {"topic": "Python", "content": "Fast code", "similarity": 0.9},
            {"topic": "JavaScript", "content": "Async patterns", "similarity": 0.8}
        ]
        
        formatted = recall_tool._format_results(results)
        
        assert "## Python" in formatted
        assert "## JavaScript" in formatted
        assert formatted.count("Similarity:") == 2