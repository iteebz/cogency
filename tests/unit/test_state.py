"""Test State contracts and behavior."""

from cogency.output import Output
from cogency.state import Cognition, State, summarize_attempts


class TestState:
    """Test State behavior and contracts."""

    def test_state_creation(self, context):
        state = State(context=context, query="test query", output=Output())

        assert state["context"] == context
        assert state["query"] == "test query"
        assert isinstance(state["output"], Output)

    def test_dict_access(self, context):
        """State should behave like a dict for backward compatibility."""
        state = State(context=context, query="test query", output=Output())

        # Test dict-like access
        assert "context" in state
        assert "query" in state
        assert "output" in state

        # Test getting items
        assert state.get("context") == context
        assert state.get("nonexistent") is None

        # Test updating
        state["new_field"] = "test_value"
        assert state["new_field"] == "test_value"

    def test_cognition_property(self, context):
        """Test that State includes Cognition as first-class property."""
        state = State(context=context, query="test query", output=Output())

        # Should have cognition by default
        assert isinstance(state.cognition, Cognition)
        assert state.cognition.react_mode == "fast"


class TestCognition:
    """Test Cognition class functionality."""

    def mock_tool_call(self, name, args):
        """Helper to create mock tool calls."""
        return {"name": name, "args": args}

    def test_cognition_update(self):
        """Test updating cognitive state with new actions."""
        cognition = Cognition()
        tool_calls = [self.mock_tool_call("search", {"query": "test"})]
        current_approach = "analytical"
        current_decision = "search for info"
        fingerprint = "search:123"
        formatted_result = "Found 3 results"

        cognition.update(
            tool_calls, current_approach, current_decision, fingerprint, formatted_result
        )

        assert cognition.current_approach == "analytical"
        assert len(cognition.iterations) == 1
        assert cognition.iterations[0]["fingerprint"] == "search:123"
        assert cognition.iterations[0]["decision"] == "search for info"
        assert cognition.iterations[0]["result"] == "Found 3 results"

    def test_cognition_update_result(self):
        """Test updating result after action execution."""
        cognition = Cognition()
        tool_calls = [self.mock_tool_call("search", {"query": "test"})]

        # Initial update without result
        cognition.update(tool_calls, "analytical", "search for info", "search:123", "")
        assert cognition.iterations[0]["result"] == ""

        # Update with result after execution
        cognition.update_result("Found 3 relevant documents")
        assert cognition.iterations[0]["result"] == "Found 3 relevant documents"

    def test_track_failure(self):
        """Test tracking failed tool attempts."""
        cognition = Cognition()
        tool_calls = [self.mock_tool_call("search", {"query": "test"})]

        cognition.track_failure(tool_calls, "poor", 2)

        assert len(cognition.failed_attempts) == 1
        failure = cognition.failed_attempts[0]
        assert failure["tool_calls"] == tool_calls
        assert failure["quality"] == "poor"
        assert failure["iteration"] == 2

    def test_tool_quality_tracking(self):
        """Test tool quality assessment tracking."""
        cognition = Cognition()

        # Initially unknown
        assert cognition.last_tool_quality == "unknown"

        # Set quality
        cognition.set_tool_quality("excellent")
        assert cognition.last_tool_quality == "excellent"

    def test_mode_switching(self):
        """Test mode switching functionality."""
        cognition = Cognition("fast")
        assert cognition.react_mode == "fast"

        # Switch mode
        cognition.switch_mode("deep", "complex problem detected")
        assert cognition.react_mode == "deep"
        assert len(cognition.mode_switches) == 1

        switch = cognition.mode_switches[0]
        assert switch["from"] == "fast"
        assert switch["to"] == "deep"
        assert switch["reason"] == "complex problem detected"

    def test_summarize_attempts(self):
        """Test summarization of failed attempts."""
        # Empty attempts
        summary = summarize_attempts([])
        assert summary == "No previous failed attempts"

        # Test with real failed attempt data (matching track_failure structure)
        failed_attempts = [
            {
                "tool_calls": [{"name": "search", "args": {"query": "test1"}}],
                "quality": "poor",
                "iteration": 1,
            },
            {
                "tool_calls": [
                    {"name": "search", "args": {"query": "test2"}},
                    {"name": "scrape", "args": {"url": "http://example.com"}},
                ],
                "quality": "failed",
                "iteration": 2,
            },
        ]

        summary = summarize_attempts(failed_attempts)
        assert "2 attempts failed" in summary
        assert "search (poor)" in summary
        assert "search, scrape (failed)" in summary

        # Test with more than 3 attempts (should only show last 3)
        many_attempts = [
            {"tool_calls": [{"name": "tool1", "args": {}}], "quality": "poor", "iteration": 1},
            {"tool_calls": [{"name": "tool2", "args": {}}], "quality": "failed", "iteration": 2},
            {"tool_calls": [{"name": "tool3", "args": {}}], "quality": "poor", "iteration": 3},
            {"tool_calls": [{"name": "tool4", "args": {}}], "quality": "failed", "iteration": 4},
        ]

        summary = summarize_attempts(many_attempts)
        assert "4 attempts failed" in summary
        # Should only show last 3
        assert "tool2 (failed)" in summary
        assert "tool3 (poor)" in summary
        assert "tool4 (failed)" in summary
        assert "tool1" not in summary  # First attempt should not appear
