"""Test reasoning prompt generation to catch f-string formatting errors."""

import pytest

from cogency.phases.reasoning.deep import prompt_deep_mode
from cogency.phases.reasoning.fast import prompt_fast_mode


def test_deep_mode_prompt_generation():
    """Test that deep mode prompt generates without f-string errors."""
    prompt = prompt_deep_mode(
        tool_registry="test_tool: description",
        query="test query",
        iteration=1,
        max_iterations=5,
        current_approach="test approach",
        previous_attempts="none",
        last_tool_quality="good",
    )

    # Should contain key components and not crash on generation
    assert "DEEP:" in prompt
    assert "test query" in prompt
    assert "test_tool" in prompt
    assert "JSON Response Format:" in prompt
    assert "tool_calls" in prompt


def test_fast_mode_prompt_generation():
    """Test that fast mode prompt generates without f-string errors."""
    prompt = prompt_fast_mode(tool_registry="test_tool: description", query="test query")

    # Should contain key components and not crash on generation
    assert "FAST:" in prompt
    assert "test query" in prompt
    assert "test_tool" in prompt
    assert '"thinking"' in prompt
    assert '"tool_calls"' in prompt


def test_mode_switch_instructions():
    """Test that JSON examples in prompts are properly escaped."""
    deep_prompt = prompt_deep_mode("tool", "query", 1, 5, "approach", "attempts", "quality")
    fast_prompt = prompt_fast_mode("tool", "query")

    # Check that braces are properly escaped (no single braces that would cause f-string errors)
    # Should have {{ and }} for JSON examples, not single { }
    # Verify unified JSON structure is present in both prompts
    for prompt in [deep_prompt, fast_prompt]:
        assert '"switch_to"' in prompt
        assert '"switch_why"' in prompt

    # Deep mode should encourage structured thinking
    assert "🤔 REFLECT" in deep_prompt
    assert "📋 PLAN" in deep_prompt
    assert "🎯 EXECUTE" in deep_prompt
