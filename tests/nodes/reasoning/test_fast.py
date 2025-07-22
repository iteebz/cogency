"""Tests for fast mode reasoning."""

from cogency.nodes.reasoning.fast import format_fast_mode, parse_fast_mode, prompt_fast_mode


def test_prompt_fast_mode():
    """Test fast mode prompt generation."""
    prompt = prompt_fast_mode("search: query", "What is Python?")
    assert "What is Python?" in prompt
    assert "search" in prompt
    assert "thinking" in prompt
    assert "decision" in prompt


def test_parse_fast_mode():
    """Test parsing fast mode responses."""
    response = '{"thinking": "Need to search", "decision": "Use search tool"}'
    result = parse_fast_mode(response)
    assert result["thinking"] == "Need to search"
    assert result["decision"] == "Use search tool"

    # Invalid JSON fallback
    response = "Invalid JSON"
    result = parse_fast_mode(response)
    assert "thinking" in result
    assert "decision" in result


def test_format_fast_mode():
    """Test formatting fast mode data."""
    data = {"thinking": "Analyzing...", "decision": "Take action"}
    formatted = format_fast_mode(data)
    assert "💭" in formatted
    assert "⚡" in formatted
    assert "Analyzing..." in formatted
    assert "Take action" in formatted
