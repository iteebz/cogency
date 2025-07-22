"""Tests for deep mode reasoning."""

from cogency.nodes.reasoning.deep import format_deep_mode, parse_deep_mode, prompt_deep_mode


def test_prompt_deep_mode():
    """Test deep mode prompt generation."""
    prompt = prompt_deep_mode(
        "search: query", "Complex question", 2, 5, "analytical", "No previous attempts", "good"
    )
    assert "Complex question" in prompt
    assert "search" in prompt
    assert "reflection" in prompt
    assert "planning" in prompt
    assert "decision" in prompt


def test_parse_deep_mode():
    """Test parsing deep mode responses."""
    response = """{"thinking": {
        "reflection": "Previous approach worked well",
        "planning": "Continue with systematic analysis",
        "decision": "Execute next step"
    }}"""
    result = parse_deep_mode(response)
    assert result["reflection"] == "Previous approach worked well"
    assert result["planning"] == "Continue with systematic analysis"
    assert result["decision"] == "Execute next step"

    # Invalid JSON fallback
    response = "Invalid JSON"
    result = parse_deep_mode(response)
    assert "reflection" in result
    assert "planning" in result
    assert "decision" in result


def test_format_deep_mode():
    """Test formatting deep mode data."""
    data = {
        "reflection": "What worked before",
        "planning": "Strategic approach",
        "decision": "Final choice",
    }
    formatted = format_deep_mode(data)
    assert "🤔" in formatted
    assert "📋" in formatted
    assert "🎯" in formatted
    assert "What worked before" in formatted
    assert "Strategic approach" in formatted
    assert "Final choice" in formatted
