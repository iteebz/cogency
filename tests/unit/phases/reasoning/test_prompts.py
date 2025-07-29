"""Test reasoning prompt generation to catch f-string formatting errors."""

import pytest

from cogency.phases.reasoning.prompt import prompt_reasoning


def test_deep_mode_prompt_generation():
    """Test that deep mode prompt generates without f-string errors."""
    prompt = prompt_reasoning(
        mode="deep",
        tool_registry="test_tool: description",
        query="test query",
        context="",
        iteration=1,
        depth=5,
        current_approach="test approach",
    )

    # Should contain key components and not crash on generation
    assert "DEEP:" in prompt
    assert "test query" in prompt
    assert "test_tool" in prompt
    assert "JSON Response Format:" in prompt
    assert "tool_calls" in prompt


def test_fast_mode_prompt_generation():
    """Test that fast mode prompt generates without f-string errors."""
    prompt = prompt_reasoning(
        mode="fast", tool_registry="test_tool: description", query="test query", context=""
    )

    # Should contain key components and not crash on generation
    assert "FAST:" in prompt
    assert "test query" in prompt
    assert "test_tool" in prompt
    assert '"thinking"' in prompt
    assert '"tool_calls"' in prompt
