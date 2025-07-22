"""Test reasoning prompt generation to catch f-string formatting errors."""

import pytest
from cogency.nodes.reasoning.deep import prompt_deep_mode
from cogency.nodes.reasoning.fast import prompt_fast_mode


def test_deep_mode_prompt_generation():
    """Test that deep mode prompt generates without f-string errors."""
    prompt = prompt_deep_mode(
        tool_info="test_tool: description",
        query="test query",
        current_iteration=1,
        max_iterations=5,
        current_approach="test approach",
        previous_attempts="none",
        last_tool_quality="good"
    )
    
    # Should contain key components and not crash on generation
    assert "DEEP MODE" in prompt
    assert "test query" in prompt
    assert "test_tool" in prompt
    assert "```json" in prompt
    assert "tool_calls" in prompt


def test_fast_mode_prompt_generation():
    """Test that fast mode prompt generates without f-string errors."""
    prompt = prompt_fast_mode(
        tool_info="test_tool: description",
        query="test query"
    )
    
    # Should contain key components and not crash on generation
    assert "FAST MODE" in prompt
    assert "test query" in prompt
    assert "test_tool" in prompt
    assert "```json" in prompt
    assert "tool_calls" in prompt


def test_prompt_json_examples_valid():
    """Test that JSON examples in prompts are properly escaped."""
    deep_prompt = prompt_deep_mode("tool", "query", 1, 5, "approach", "attempts", "quality")
    fast_prompt = prompt_fast_mode("tool", "query")
    
    # Check that braces are properly escaped (no single braces that would cause f-string errors)
    # Should have {{ and }} for JSON examples, not single { }
    assert "{{" in deep_prompt
    assert "}}" in deep_prompt
    assert "{{" in fast_prompt
    assert "}}" in fast_prompt
    
    # Verify specific JSON structure indicators are present
    assert '"thinking"' in deep_prompt
    assert '"tool_calls"' in deep_prompt
    assert '"thinking"' in fast_prompt
    assert '"tool_calls"' in fast_prompt