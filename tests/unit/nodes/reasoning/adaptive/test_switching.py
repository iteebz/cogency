"""Tests for bidirectional mode switching logic."""

import pytest

from cogency.nodes.reasoning.adaptive.switching import (
    parse_switch,
    should_switch,
    switch_mode,
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


def test_context_preservation_during_switch():
    """Test that switching modes preserves all context."""
    from cogency.context import Context
    from cogency.state import State

    # Create state with some iterations
    context = Context("test query")
    state = State(context=context, query="test")

    # Add multiple iterations
    iterations = [
        {
            "iteration": 1,
            "decision": "search for info",
            "fingerprint": "search:123",
            "tool_calls": [],
            "result": "found 3 results",
        },
        {
            "iteration": 2,
            "decision": "analyze data",
            "fingerprint": "analyze:456",
            "tool_calls": [],
            "result": "patterns identified",
        },
        {
            "iteration": 3,
            "decision": "verify findings",
            "fingerprint": "verify:789",
            "tool_calls": [],
            "result": "confirmed",
        },
        {
            "iteration": 4,
            "decision": "synthesize",
            "fingerprint": "synth:101",
            "tool_calls": [],
            "result": "complete",
        },
        {
            "iteration": 5,
            "decision": "final check",
            "fingerprint": "check:112",
            "tool_calls": [],
            "result": "validated",
        },
    ]

    state.iterations = iterations.copy()
    state.react_mode = "fast"

    # Switch to deep mode
    result = switch_mode(state, "deep", "needs deeper analysis")

    # Verify mode changed
    assert result["react_mode"] == "deep"
    assert state.react_mode == "deep"

    # Verify ALL iterations preserved
    assert len(state.iterations) == 5
    assert state.iterations == iterations

    # Switch back to fast
    switch_mode(state, "fast", "simpler approach")

    # Verify ALL iterations still preserved
    assert len(state.iterations) == 5
    assert state.iterations == iterations
    assert state.react_mode == "fast"


