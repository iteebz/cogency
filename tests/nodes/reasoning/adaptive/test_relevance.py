"""Test relevance scoring business logic."""

import pytest
from unittest.mock import Mock

from cogency.nodes.reasoning.adaptive.relevance import (
    relevant_context,
    score_memory_relevance,
)


from tests.conftest import MockLLM


@pytest.mark.asyncio
async def test_memory_relevance_scoring():
    """Test memory item scoring."""
    memory_items = [
        {"content": "User prefers Python for data analysis"},
        {"content": "User lives in San Francisco"},
        {"content": "User is learning machine learning"},
    ]

    llm_response = """{"0": 0.9, "1": 0.2, "2": 0.8}"""
    llm_client = MockLLM(llm_response)

    scored_items = await score_memory_relevance(
        "Help me with Python data analysis", memory_items, llm_client, max_items=3
    )

    # Should be sorted by relevance
    assert len(scored_items) == 3
    assert scored_items[0]["content"] == "User prefers Python for data analysis"
    assert scored_items[0]["relevance_score"] == 0.9
    assert scored_items[1]["relevance_score"] == 0.8


@pytest.mark.asyncio
async def test_relevance_edge_cases():
    """Test edge cases in relevance scoring."""
    # Empty memory
    llm_client = MockLLM("{}")
    scored_items = await score_memory_relevance("test query", [], llm_client)
    assert scored_items == []

    # Invalid LLM response
    memory_items = [{"content": "Item 1"}, {"content": "Item 2"}]
    llm_client = MockLLM("Invalid JSON response")
    scored_items = await score_memory_relevance("test query", memory_items, llm_client, max_items=5)
    assert len(scored_items) == 2


@pytest.mark.asyncio
async def test_relevant_context_fast_mode():
    """Test fast mode context retrieval."""
    cognition = {
        "decision_history": ["decision1", "decision2", "decision3", "decision4"],
        "failed_attempts": ["fail1", "fail2", "fail3"],
    }

    context = await relevant_context(cognition, "test query", "fast", None)

    # Fast mode uses FIFO
    assert len(context["recent_decisions"]) == 3
    assert context["recent_decisions"] == ["decision2", "decision3", "decision4"]
    assert len(context["recent_failures"]) == 2


@pytest.mark.asyncio
async def test_relevant_context_deep_mode():
    """Test deep mode context retrieval."""
    cognition = {
        "decision_history": ["search python", "analyze data", "write code"],
        "failed_attempts": ["failed search", "syntax error"],
    }

    llm_response = """{"0": 0.9, "1": 0.5, "2": 0.8, "3": 0.3, "4": 0.7}"""
    llm_client = MockLLM(llm_response)

    context = await relevant_context(cognition, "help with python programming", "deep", llm_client)

    assert "recent_decisions" in context
    assert "recent_failures" in context


@pytest.mark.asyncio
async def test_context_edge_cases():
    """Test context retrieval edge cases."""
    # Empty cognition
    cognition = {}
    context = await relevant_context(cognition, "test query", "fast", None)
    assert context["recent_decisions"] == []
    assert context["recent_failures"] == []

    # Deep mode LLM failure
    cognition = {"decision_history": ["decision1"], "failed_attempts": ["fail1"]}
    llm_client = Mock()
    llm_client.run.side_effect = Exception("LLM error")

    context = await relevant_context(cognition, "test query", "deep", llm_client)
    assert "recent_decisions" in context
    assert "recent_failures" in context
