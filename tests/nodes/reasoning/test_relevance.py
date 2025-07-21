"""Tests for LLM-based memory relevance scoring."""

from unittest.mock import Mock

from cogency.nodes.reasoning.relevance import relevant_context, score_memory_relevance


class MockLLM:
    """Mock LLM client for testing."""

    def __init__(self, response):
        self.response = response

    def run(self, messages):
        return self.response


class TestScoreMemoryRelevance:
    """Test LLM-based relevance scoring."""

    def test_score_memory_items(self):
        """Test basic memory item scoring."""
        memory_items = [
            {"content": "User prefers Python for data analysis"},
            {"content": "User lives in San Francisco"},
            {"content": "User is learning machine learning"},
        ]

        # Mock LLM response with scores
        llm_response = """Based on the query, here are the relevance scores:
        {
          "0": 0.9,
          "1": 0.2,
          "2": 0.8
        }"""

        llm_client = MockLLM(llm_response)

        scored_items = score_memory_relevance(
            "Help me with Python data analysis", memory_items, llm_client, max_items=3
        )

        # Should be sorted by relevance (highest first)
        assert len(scored_items) == 3
        assert scored_items[0]["content"] == "User prefers Python for data analysis"
        assert scored_items[0]["relevance_score"] == 0.9
        assert scored_items[1]["content"] == "User is learning machine learning"
        assert scored_items[1]["relevance_score"] == 0.8
        assert scored_items[2]["content"] == "User lives in San Francisco"
        assert scored_items[2]["relevance_score"] == 0.2

    def test_max_items_limit(self):
        """Test max items limit is respected."""
        memory_items = [{"content": f"Item {i}"} for i in range(10)]

        llm_response = """{"0": 0.9, "1": 0.8, "2": 0.7, "3": 0.6, "4": 0.5}"""
        llm_client = MockLLM(llm_response)

        scored_items = score_memory_relevance("test query", memory_items, llm_client, max_items=3)

        assert len(scored_items) == 3

    def test_empty_memory_items(self):
        """Test handling empty memory items."""
        llm_client = MockLLM("{}")

        scored_items = score_memory_relevance("test query", [], llm_client)

        assert scored_items == []

    def test_invalid_llm_response(self):
        """Test fallback when LLM response is invalid."""
        memory_items = [{"content": "Item 1"}, {"content": "Item 2"}]

        llm_client = MockLLM("Invalid JSON response")

        scored_items = score_memory_relevance("test query", memory_items, llm_client, max_items=5)

        # Should return original items unchanged
        assert len(scored_items) == 2
        assert scored_items[0]["content"] == "Item 1"
        assert scored_items[1]["content"] == "Item 2"


class TestGetRelevantContext:
    """Test relevant context retrieval."""

    def test_fast_mode_fifo(self):
        """Test fast mode uses simple FIFO."""
        cognition = {
            "action_history": ["action1", "action2", "action3", "action4"],
            "failed_attempts": ["fail1", "fail2", "fail3"],
        }

        context = relevant_context(
            cognition,
            "test query",
            "fast",
            None,  # No LLM needed for fast mode
        )

        # Fast mode: max 3 recent actions, 2 recent failures
        assert len(context["recent_actions"]) == 3
        assert context["recent_actions"] == ["action2", "action3", "action4"]
        assert len(context["recent_failures"]) == 2
        assert context["recent_failures"] == ["fail2", "fail3"]

    def test_deep_mode_llm_scoring(self):
        """Test deep mode uses LLM-based relevance scoring."""
        cognition = {
            "action_history": ["search python", "analyze data", "write code"],
            "failed_attempts": ["failed search", "syntax error"],
        }

        # Mock LLM response for relevance scoring
        llm_response = """{"0": 0.9, "1": 0.5, "2": 0.8, "3": 0.3, "4": 0.7}"""
        llm_client = MockLLM(llm_response)

        context = relevant_context(cognition, "help with python programming", "deep", llm_client)

        # Should have relevant actions and failures based on LLM scoring
        assert "recent_actions" in context
        assert "recent_failures" in context
        assert isinstance(context["recent_actions"], list)
        assert isinstance(context["recent_failures"], list)

    def test_deep_mode_fallback(self):
        """Test deep mode fallback when LLM fails."""
        cognition = {"action_history": ["action1", "action2"], "failed_attempts": ["fail1"]}

        # Mock LLM that raises exception
        llm_client = Mock()
        llm_client.run.side_effect = Exception("LLM error")

        context = relevant_context(cognition, "test query", "deep", llm_client)

        # Should fallback to FIFO with deep mode limits
        assert "recent_actions" in context
        assert "recent_failures" in context
        assert len(context["recent_actions"]) <= 10  # Deep mode limit

    def test_empty_cognition(self):
        """Test handling empty cognitive state."""
        cognition = {}

        context = relevant_context(cognition, "test query", "fast", None)

        assert context["recent_actions"] == []
        assert context["recent_failures"] == []
