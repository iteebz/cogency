"""Tests for fast mode reasoning."""

from cogency.nodes.reasoning.fast import prompt_fast_mode


def test_prompt():
    """Test fast mode prompt generation."""
    prompt = prompt_fast_mode("search: query", "What is Python?")
    assert "What is Python?" in prompt
    assert "search" in prompt
    assert "thinking" in prompt
