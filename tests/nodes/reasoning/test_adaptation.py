"""Tests for bidirectional mode switching logic."""
import pytest
from cogency.nodes.reasoning.adaptation import (
    get_mode_switch,
    should_switch,
    switch_mode,
    get_switch_prompt
)


class TestModeSwitch:
    """Test mode switch extraction from LLM responses."""
    
    def test_extract_mode_switch_to_deep(self):
        """Test extracting switch to deep mode."""
        response = '''This task requires deeper analysis than I thought.
        {"switch_to": "deep", "switch_reason": "complex synthesis needed"}'''
        
        mode, reason = get_mode_switch(response)
        assert mode == "deep"
        assert reason == "complex synthesis needed"
    
    def test_extract_mode_switch_to_fast(self):
        """Test extracting switch to fast mode.""" 
        response = '''Actually this is just a simple lookup.
        {"switch_to": "fast", "switch_reason": "simpler than expected"}'''
        
        mode, reason = get_mode_switch(response)
        assert mode == "fast"
        assert reason == "simpler than expected"
    
    def test_extract_no_mode_switch(self):
        """Test when no mode switch is requested."""
        response = '''I'll continue with the current approach.
        {"reasoning": "making progress with current strategy"}'''
        
        mode, reason = get_mode_switch(response)
        assert mode is None
        assert reason is None
    
    def test_extract_invalid_json(self):
        """Test graceful handling of invalid JSON."""
        response = '''{"switch_to": "deep", invalid json'''
        
        mode, reason = get_mode_switch(response)
        assert mode is None
        assert reason is None


class TestShouldSwitch:
    """Test mode switching decision logic."""
    
    def test_should_switch_fast_to_deep(self):
        """Test switching from fast to deep mode."""
        should_switch = should_switch(
            current_mode="fast",
            switch_to="deep", 
            switch_reason="needs complex analysis",
            current_iteration=2
        )
        assert should_switch is True
    
    def test_should_switch_deep_to_fast(self):
        """Test switching from deep to fast mode."""
        should_switch = should_switch(
            current_mode="deep",
            switch_to="fast",
            switch_reason="simpler than expected", 
            current_iteration=1
        )
        assert should_switch is True
    
    def test_no_switch_same_mode(self):
        """Test no switching when requesting same mode."""
        should_switch = should_switch(
            current_mode="fast",
            switch_to="fast",
            switch_reason="continue current approach",
            current_iteration=1
        )
        assert should_switch is False
    
    def test_no_switch_late_iteration(self):
        """Test preventing switches in late iterations."""
        should_switch = should_switch(
            current_mode="fast", 
            switch_to="deep",
            switch_reason="needs analysis",
            current_iteration=4  # Close to max iterations
        )
        assert should_switch is False


class TestExecuteSwitch:
    """Test mode switch execution."""
    
    def test_execute_switch_to_deep(self):
        """Test switching to deep mode updates state correctly."""
        state = {
            'react_mode': 'fast',
            'cognition': {
                'react_mode': 'fast',
                'max_history': 3,
                'max_failures': 5
            }
        }
        
        updated_state = switch_mode(
            state, 
            new_mode="deep",
            switch_reason="complex task detected"
        )
        
        assert updated_state['react_mode'] == 'deep'
        assert updated_state['cognition']['react_mode'] == 'deep'
        assert updated_state['cognition']['max_history'] == 10
        assert updated_state['cognition']['max_failures'] == 15
    
    def test_execute_switch_to_fast(self):
        """Test switching to fast mode updates state correctly."""
        state = {
            'react_mode': 'deep', 
            'cognition': {
                'react_mode': 'deep',
                'max_history': 10,
                'max_failures': 15
            }
        }
        
        updated_state = switch_mode(
            state,
            new_mode="fast", 
            switch_reason="task simpler than expected"
        )
        
        assert updated_state['react_mode'] == 'fast'
        assert updated_state['cognition']['react_mode'] == 'fast'
        assert updated_state['cognition']['max_history'] == 3
        assert updated_state['cognition']['max_failures'] == 5


class TestPromptAddition:
    """Test mode switch prompt additions."""
    
    def test_fast_mode_prompt_addition(self):
        """Test fast mode gets switching capability."""
        addition = get_switch_prompt("fast")
        
        assert "deep" in addition.lower()
        assert "complex" in addition.lower() or "analysis" in addition.lower()
    
    def test_deep_mode_prompt_addition(self):
        """Test deep mode gets downshift capability."""
        addition = get_switch_prompt("deep")
        
        assert "fast" in addition.lower()
        assert "simple" in addition.lower() or "efficient" in addition.lower()