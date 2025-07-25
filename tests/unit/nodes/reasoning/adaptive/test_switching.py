"""Tests for bidirectional mode switching logic."""

import pytest

from cogency.nodes.reasoning.adaptive.switching import (
    parse_switch,
    should_switch,
    switch_mode,
    switch_prompt,
)


def test_parse_switch():
    """Test parsing mode switch from LLM responses."""
    # Valid JSON switch
    response = """This task requires deeper analysis.
    ```json
    {"switch_to": "deep", "switch_why": "complex synthesis needed"}
    ```"""

    mode, reason = parse_switch(response)
    assert mode == "deep"
    assert reason == "complex synthesis needed"

    # No switch
    response = """{"reasoning": "making progress with current strategy"}"""
    mode, reason = parse_switch(response)
    assert mode is None
    assert reason is None


def test_should_switch():
    """Test switch decision logic."""
    # Should switch from fast to deep for complex tasks
    assert should_switch("fast", "deep", "complex analysis required", 1) is True

    # Should switch from deep to fast for simple tasks
    assert should_switch("deep", "fast", "simpler than expected", 2) is True

    # Should not switch to same mode
    assert should_switch("fast", "fast", "reason", 1) is False


def test_switch_mode():
    """Test mode switching execution."""
    # Switch from fast to deep
    state = {"react_mode": "fast"}
    result = switch_mode(state, "deep", "needs deeper analysis")
    assert result["react_mode"] == "deep"

    # Check state is modified
    assert state["react_mode"] == "deep"


def test_switch_prompt():
    """Test switch prompt generation."""
    # Fast mode prompt
    prompt = switch_prompt("fast")
    assert "switch_to" in prompt
    assert "switch_reason" in prompt
    assert "deep" in prompt

    # Deep mode prompt
    prompt = switch_prompt("deep")
    assert "switch_to" in prompt
    assert "downshift to fast" in prompt
