"""Comprehensive reasoning system tests - fast, deep, and unified modes."""

import pytest

from cogency.nodes.reasoning.deep import prompt_deep_mode
from cogency.nodes.reasoning.fast import prompt_fast_mode
from cogency.nodes.reasoning.parser import format_thinking, parse_response_result


def test_fast_prompt_generation():
    prompt = prompt_fast_mode("search: query", "What is Python?")
    assert "What is Python?" in prompt
    assert "search" in prompt
    assert "thinking" in prompt


def test_deep_prompt_generation():
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


def test_unified_json_structure():
    response = """{
        "thinking": "analyzing the problem",
        "tool_calls": [{"name": "search", "args": {"query": "test"}}],
        "switch_to": null,
        "switch_why": null
    }"""

    from cogency.utils.parsing import parse_json

    fast_parsed = parse_json(response).data
    deep_parsed = parse_json(response).data

    assert fast_parsed["thinking"] == "analyzing the problem"
    assert deep_parsed["thinking"] == "analyzing the problem"
    assert fast_parsed["switch_to"] is None
    assert deep_parsed["switch_to"] is None


def test_deep_mode_structured_thinking():
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
    malformed = "not json at all"
    result = parse_response_result(malformed)

    assert result.success
    assert result.data["thinking"] == "Processing request..."
    assert result.data["switch_to"] is None
    assert result.data["tool_calls"] == []


def test_formatting():
    data = {"thinking": "test thought"}

    fast_formatted = format_thinking(data["thinking"], mode="fast")
    deep_formatted = format_thinking(data["thinking"], mode="deep")

    assert "💭" in fast_formatted
    assert "🧠" in deep_formatted
    assert "test thought" in fast_formatted
    assert "test thought" in deep_formatted
