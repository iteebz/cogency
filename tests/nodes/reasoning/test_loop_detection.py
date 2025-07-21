"""Tests for loop detection functionality."""
import pytest
from cogency.nodes.reasoning.loop_detection import action_fingerprint, detect_loop, detect_fast_loop


class MockToolCall:
    """Mock tool call for testing."""
    def __init__(self, name, args):
        self.name = name
        self.args = args


class TestActionFingerprinting:
    """Test action fingerprinting for loop detection."""
    
    def test_empty_tool_calls(self):
        """Test fingerprinting with no tool calls."""
        result = action_fingerprint([])
        assert result == "no_action"
    
    def test_single_tool_call(self):
        """Test fingerprinting with single tool call."""
        tool_calls = [MockToolCall("search", {"query": "test"})]
        result = action_fingerprint(tool_calls)
        assert result.startswith("search:")
        # Just check that the fingerprint contains a hash (numbers)
    
    def test_multiple_tool_calls(self):
        """Test fingerprinting with multiple tool calls."""
        tool_calls = [
            MockToolCall("search", {"query": "test1"}),
            MockToolCall("scrape", {"url": "http://example.com"})
        ]
        result = action_fingerprint(tool_calls)
        assert "|" in result
        assert "search:" in result
        assert "scrape:" in result
    
    def test_identical_calls_same_fingerprint(self):
        """Test that identical calls produce same fingerprint."""
        tool_calls1 = [MockToolCall("search", {"query": "test"})]
        tool_calls2 = [MockToolCall("search", {"query": "test"})]
        
        fp1 = action_fingerprint(tool_calls1)
        fp2 = action_fingerprint(tool_calls2)
        
        assert fp1 == fp2
    
    def test_different_calls_different_fingerprint(self):
        """Test that different calls produce different fingerprints."""
        tool_calls1 = [MockToolCall("search", {"query": "test1"})]
        tool_calls2 = [MockToolCall("search", {"query": "test2"})]
        
        fp1 = action_fingerprint(tool_calls1)
        fp2 = action_fingerprint(tool_calls2)
        
        assert fp1 != fp2


class TestLoopDetection:
    """Test loop detection logic."""
    
    @pytest.mark.parametrize("action_history,expected", [
        # No loop cases
        (["action1", "action2"], False),  # Insufficient history
        (["action1", "action2", "action3"], False),  # Different actions
        (["action1", "action2", "action3"], False),  # No A-B-A pattern
        ([], False),  # Empty history
        
        # Loop cases
        (["action1", "action1", "action1"], True),  # Identical repeated actions
        (["action1", "action2", "action1"], True),  # A-B-A pattern
    ])
    def test_loop_detection(self, action_history, expected):
        """Test loop detection with various action histories."""
        cognition = {"action_history": action_history}
        assert detect_loop(cognition) is expected
    
    def test_missing_action_history(self):
        """Test no loop with missing action history key."""
        cognition = {}
        assert not detect_loop(cognition)


class TestFastLoopDetection:
    """Test fast loop detection logic."""
    
    def test_fast_loop_detection(self):
        """Test fast loop detection with various action histories."""
        # No loop case
        cognition = {"action_history": ["action1", "action2"]}
        assert not detect_fast_loop(cognition)
        
        # Loop case - repeated actions
        cognition = {"action_history": ["action1", "action1"]}
        assert detect_fast_loop(cognition)
        
        # Empty history
        cognition = {"action_history": []}
        assert not detect_fast_loop(cognition)
        
        # Missing action history
        cognition = {}
        assert not detect_fast_loop(cognition)