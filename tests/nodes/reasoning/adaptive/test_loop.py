"""Tests for loop detection functionality."""

from cogency.nodes.reasoning.adaptive import action_fingerprint, detect_fast_loop, detect_loop


class MockToolCall:
    def __init__(self, name, args):
        self.name = name
        self.args = args


def test_action_fingerprint():
    """Test action fingerprinting."""
    # Empty tool calls
    assert action_fingerprint([]) == "no_action"

    # Single tool call
    tool_calls = [MockToolCall("search", {"query": "test"})]
    result = action_fingerprint(tool_calls)
    assert result.startswith("search:")

    # Multiple tool calls
    tool_calls = [
        MockToolCall("search", {"query": "test1"}),
        MockToolCall("scrape", {"url": "http://example.com"}),
    ]
    result = action_fingerprint(tool_calls)
    assert "|" in result and "search:" in result and "scrape:" in result

    # Identical calls produce same fingerprint
    fp1 = action_fingerprint([MockToolCall("search", {"query": "test"})])
    fp2 = action_fingerprint([MockToolCall("search", {"query": "test"})])
    assert fp1 == fp2


def test_fast_loop_detection():
    """Test fast loop detection."""
    # Should detect immediate loop
    cognition = {"action_fingerprints": ["search:123", "search:123"]}
    is_loop = detect_fast_loop(cognition)
    assert is_loop is True

    # No loop in short history
    cognition = {"action_fingerprints": ["search:123", "scrape:456"]}
    is_loop = detect_fast_loop(cognition)
    assert is_loop is False


def test_comprehensive_loop_detection():
    """Test comprehensive loop detection."""
    # Pattern loop (A-B-A)
    cognition = {"action_fingerprints": ["search:123", "scrape:456", "search:123"]}
    is_loop = detect_loop(cognition)
    assert is_loop is True

    # No loop detected
    cognition = {"action_fingerprints": ["search:123", "scrape:456", "analyze:789"]}
    is_loop = detect_loop(cognition)
    assert is_loop is False

    # Repeated identical actions
    cognition = {"action_fingerprints": ["search:123", "search:123", "search:123"]}
    is_loop = detect_loop(cognition)
    assert is_loop is True


def test_loop_empty_history():
    """Test loop detection with minimal history."""
    # Empty history
    cognition = {"action_fingerprints": []}
    assert detect_loop(cognition) is False
    assert detect_fast_loop(cognition) is False
