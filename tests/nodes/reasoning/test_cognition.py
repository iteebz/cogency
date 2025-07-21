"""Tests for cognitive state management."""
import pytest
from unittest.mock import MagicMock
from cogency.nodes.reasoning.cognition import update_cognition, summarize_attempts, track_failure


class TestCognitionUpdates:
    """Test cognitive state updates."""


class TestCognitionUpdates:
    """Test cognitive state updates."""
    
    def test_update_cognition(self):
        """Test updating cognitive state with new actions."""
        cognition = {
            "strategy_history": [],
            "action_history": [],
            "max_history": 5
        }
        
        class MockToolCall:
            def __init__(self, name, args):
                self.name = name
                self.args = args
        
        tool_calls = [MockToolCall("search", {"query": "test"})]
        fingerprint = "search:123"
        
        update_cognition(cognition, tool_calls, "new_strategy", fingerprint)
        
        assert len(cognition["strategy_history"]) == 1
        assert cognition["strategy_history"][0] == "new_strategy"
        assert len(cognition["action_history"]) == 1
        assert cognition["action_history"][0] == fingerprint
    
    def test_update_cognition_memory_limit(self):
        """Test memory limits are enforced during updates."""
        cognition = {
            "strategy_history": ["s1", "s2", "s3", "s4", "s5"],
            "action_history": ["a1", "a2", "a3", "a4", "a5"],
            "max_history": 5
        }
        
        class MockToolCall:
            def __init__(self, name, args):
                self.name = name
                self.args = args
        
        tool_calls = [MockToolCall("search", {"query": "test"})]
        fingerprint = "search:123"
        
        update_cognition(cognition, tool_calls, "new_strategy", fingerprint)
        
        # Should maintain max_history limit
        assert len(cognition["strategy_history"]) == 5
        assert len(cognition["action_history"]) == 5
        # Should have newest items
        assert cognition["strategy_history"][-1] == "new_strategy"
        assert cognition["action_history"][-1] == fingerprint
        # Should have removed oldest items
        assert "s1" not in cognition["strategy_history"]
        assert "a1" not in cognition["action_history"]


class TestFailureTracking:
    """Test failure tracking functionality."""
    
    def test_track_failure(self):
        """Test tracking failed tool attempts."""
        cognition = {
            "failed_attempts": [],
            "max_failures": 5
        }
        
        class MockToolCall:
            def __init__(self, name, args):
                self.name = name
                self.args = args
                
            def get(self, key, default=None):
                if key == "function":
                    return {"name": self.name}
                return default
        
        tool_calls = [MockToolCall("search", {"query": "test"})]
        
        track_failure(cognition, tool_calls, "poor", 2)
        
        assert len(cognition["failed_attempts"]) == 1
        failure = cognition["failed_attempts"][0]
        assert failure["tool"] == "search"
        assert failure["reason"] == "poor"
        assert failure["iteration"] == 2
    
    def test_track_failure_memory_limit(self):
        """Test failure tracking respects memory limits."""
        cognition = {
            "failed_attempts": [
                {"tool": f"tool{i}", "reason": "error", "iteration": i} 
                for i in range(5)
            ],
            "max_failures": 5
        }
        
        class MockToolCall:
            def __init__(self, name, args):
                self.name = name
                self.args = args
                
            def get(self, key, default=None):
                if key == "function":
                    return {"name": self.name}
                return default
        
        tool_calls = [MockToolCall("new_tool", {"query": "test"})]
        
        track_failure(cognition, tool_calls, "failed", 6)
        
        # Should maintain max_failures limit
        assert len(cognition["failed_attempts"]) == 5
        # Should have newest failure
        assert cognition["failed_attempts"][-1]["tool"] == "new_tool"
        # Should have removed oldest failure
        assert not any(f["tool"] == "tool0" for f in cognition["failed_attempts"])


class TestAttemptsSummarization:
    """Test summarization of failed attempts."""
    
    def test_summarize_attempts_empty(self):
        """Test summarizing empty attempts list."""
        summary = summarize_attempts([])
        assert summary == "No previous failed attempts"
    
    def test_summarize_attempts(self):
        """Test summarizing failed attempts."""
        attempts = [
            {"tool": "search", "reason": "poor", "iteration": 1, "args": {"query": "test1"}},
            {"tool": "scrape", "reason": "failed", "iteration": 2, "args": {"url": "example.com"}}
        ]
        
        summary = summarize_attempts(attempts)
        
        assert "search" in summary
        assert "scrape" in summary
        assert "poor" in summary
        assert "failed" in summary
        # The implementation doesn't include args in the summary
        assert "Previous failed attempts:" in summary