"""Comprehensive reasoning system tests - fast, deep, and unified modes."""

import pytest

from cogency.phases.reasoning.prompt import prompt_reasoning
from cogency.utils.parsing import parse_json


def test_fast_prompt_generation():
    prompt = prompt_reasoning(mode="fast", tool_registry="search: query", query="What is Python?", context="")
    assert "What is Python?" in prompt
    assert "search" in prompt
    assert "thinking" in prompt


def test_deep_prompt_generation():
    prompt = prompt_reasoning(
        mode="deep",
        tool_registry="search: query",
        query="Complex question",
        iteration=2,
        max_iterations=5,
        current_approach="analytical",
        context="No previous attempts",
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
        "switch_why": null,
        "summary_update": {
            "goal": "",
            "progress": "",
            "current_approach": "",
            "key_findings": "",
            "next_focus": ""
        }
    }"""

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
        "switch_why": null,
        "summary_update": {
            "goal": "",
            "progress": "",
            "current_approach": "",
            "key_findings": "",
            "next_focus": ""
        }
    }"""

    parsed = parse_json(response).data
    assert "REFLECTION" in parsed["thinking"]
    assert "PLANNING" in parsed["thinking"]
    assert "DECISION" in parsed["thinking"]


def test_mode_switching():
    switch_response = """{
        "thinking": "This task needs deeper analysis",
        "tool_calls": [],
        "switch_to": "deep",
        "switch_why": "complex multi-step reasoning required",
        "summary_update": {
            "goal": "",
            "progress": "",
            "current_approach": "",
            "key_findings": "",
            "next_focus": ""
        }
    }"""

    parsed = parse_json(switch_response).data
    assert parsed["switch_to"] == "deep"
    assert parsed["switch_why"] == "complex multi-step reasoning required"


def test_parsing_fallback():
    malformed = "not json at all"
    result = parse_json(malformed)

    assert not result.success
    assert result.data is None