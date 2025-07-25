"""Tests for deep mode reasoning."""

from cogency.nodes.reasoning.deep import prompt_deep_mode


def test_prompt():
    """Test deep mode prompt generation."""
    prompt = prompt_deep_mode(
        "search: query",
        "Complex question",
        2,
        5,
        "analytical",
        "No previous attempts",
        "good",
    )
    assert "Complex question" in prompt
    assert "search" in prompt
    assert "🤔 REFLECT:" in prompt
    assert "📋 PLAN:" in prompt
    assert "🎯 EXECUTE:" in prompt
    assert "DEEP:" in prompt
    assert "DOWNSHIFT" in prompt
