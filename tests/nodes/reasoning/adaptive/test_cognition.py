"""Test cognitive state management."""

from cogency.nodes.reasoning.adaptive.cognition import (
    summarize_attempts,
    track_failure,
    update_cognition,
)


class MockToolCall:
    def __init__(self, name, args):
        self.name = name
        self.args = args

    def get(self, key, default=None):
        if key == "function":
            return {"name": self.name}
        return default


def test_update_cognition():
    """Test updating cognitive state with new actions."""
    cognition = {"approach_history": [], "decision_history": [], "action_fingerprints": []}
    tool_calls = [MockToolCall("search", {"query": "test"})]
    current_approach = "analytical"
    current_decision = "search for info"
    fingerprint = "search:123"

    update_cognition(cognition, tool_calls, current_approach, current_decision, fingerprint)

    assert len(cognition["approach_history"]) == 1
    assert cognition["approach_history"][0] == "analytical"
    assert len(cognition["decision_history"]) == 1
    assert cognition["decision_history"][0] == "search for info"
    assert len(cognition["action_fingerprints"]) == 1
    assert cognition["action_fingerprints"][0] == "search:123"


def test_cognition_memory_limits():
    """Test memory limits are enforced."""
    cognition = {
        "approach_history": ["a1", "a2", "a3", "a4", "a5"],
        "decision_history": ["d1", "d2", "d3", "d4", "d5"],
        "action_fingerprints": ["f1", "f2", "f3", "f4", "f5"],
        "max_history": 5,
    }

    tool_calls = [MockToolCall("search", {"query": "test"})]
    current_approach = "new_approach"
    current_decision = "new_decision"
    fingerprint = "search:123"

    update_cognition(cognition, tool_calls, current_approach, current_decision, fingerprint)

    # Should maintain max_history limit
    assert len(cognition["approach_history"]) == 5
    assert len(cognition["decision_history"]) == 5
    assert len(cognition["action_fingerprints"]) == 5
    assert cognition["approach_history"][-1] == "new_approach"
    assert cognition["decision_history"][-1] == "new_decision"
    assert cognition["action_fingerprints"][-1] == "search:123"


def test_track_failure():
    """Test tracking failed tool attempts."""
    cognition = {"failed_attempts": [], "max_failures": 5}
    tool_calls = [MockToolCall("search", {"query": "test"})]

    track_failure(cognition, tool_calls, "poor", 2)

    assert len(cognition["failed_attempts"]) == 1
    failure = cognition["failed_attempts"][0]
    assert failure["tool"] == "search"
    assert failure["reason"] == "poor"
    assert failure["iteration"] == 2


def test_failure_memory_limits():
    """Test failure tracking respects memory limits."""
    cognition = {
        "failed_attempts": [
            {"tool": f"tool{i}", "reason": "error", "iteration": i} for i in range(5)
        ],
        "max_failures": 5,
    }

    tool_calls = [MockToolCall("new_tool", {"query": "test"})]
    track_failure(cognition, tool_calls, "failed", 6)

    # Should maintain max_failures limit
    assert len(cognition["failed_attempts"]) == 5
    assert cognition["failed_attempts"][-1]["tool"] == "new_tool"


def test_summarize_attempts():
    """Test summarization of failed attempts."""
    # Empty attempts
    summary = summarize_attempts([])
    assert summary == "No previous failed attempts"

    # Failed attempts
    attempts = [
        {"tool": "search", "reason": "poor", "iteration": 1, "args": {"query": "test1"}},
        {"tool": "scrape", "reason": "failed", "iteration": 2, "args": {"url": "example.com"}},
    ]

    summary = summarize_attempts(attempts)
    assert "search" in summary
    assert "scrape" in summary
    assert "poor" in summary
    assert "failed" in summary
    assert "Previous failed attempts:" in summary
