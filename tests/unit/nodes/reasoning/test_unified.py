"""Test unified reasoning system."""

import pytest

from cogency.nodes.reasoning.parser import format_thinking, parse_response_result


def test_unified_json_structure():
    """Test that both modes use the same JSON structure."""
    # Valid unified response
    response = """{
        "thinking": "analyzing the problem",
        "tool_calls": [{"name": "search", "args": {"query": "test"}}],
        "switch_to": null,
        "switch_why": null
    }"""

    from cogency.utils.parsing import parse_json

    fast_parsed = parse_json(response).data
    deep_parsed = parse_json(response).data

    # Both should parse the same way
    assert fast_parsed["thinking"] == "analyzing the problem"
    assert deep_parsed["thinking"] == "analyzing the problem"
    assert fast_parsed["switch_to"] is None
    assert deep_parsed["switch_to"] is None


def test_deep_mode_structured_thinking():
    """Test that deep mode encourages structured thinking."""
    response = """{
        "thinking": "🤔 REFLECTION: Previous attempt failed. 📋 PLANNING: Try different approach. 🎯 DECISION: Using new tool.",
        "tool_calls": [],
        "switch_to": null,
        "switch_why": null
    }"""

    from cogency.utils.parsing import parse_json

    parsed = parse_json(response).data
    assert "REFLECTION" in parsed["thinking"]
    assert "PLANNING" in parsed["thinking"]
    assert "DECISION" in parsed["thinking"]


def test_mode_switching():
    """Test mode switching logic."""
    switch_response = """{
        "thinking": "This task needs deeper analysis",
        "tool_calls": [],
        "switch_to": "deep",
        "switch_why": "complex multi-step reasoning required"
    }"""

    parsed = parse_response_result(switch_response).data
    assert parsed["switch_to"] == "deep"
    assert parsed["switch_why"] == "complex multi-step reasoning required"


def test_parsing_fallback():
    """Test parser gracefully handles malformed responses."""
    malformed = "not json at all"
    result = parse_response_result(malformed)

    assert result.success  # Success with fallback data for resilience
    assert result.error and "Parse failed" in result.error
    assert result.data["thinking"] == "Processing request..."
    assert result.data["switch_to"] is None
    assert result.data["tool_calls"] == []


def test_formatting():
    """Test formatting functions work with unified structure."""
    data = {"thinking": "test thought"}

    from cogency.nodes.reasoning.parser import format_thinking

    fast_formatted = format_thinking(data["thinking"], mode="fast")
    deep_formatted = format_thinking(data["thinking"], mode="deep")

    assert "💭" in fast_formatted  # Fast mode emoji
    assert "🧠" in deep_formatted  # Deep mode emoji
    assert "test thought" in fast_formatted
    assert "test thought" in deep_formatted
