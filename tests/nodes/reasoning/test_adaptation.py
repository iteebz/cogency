"""Tests for bidirectional mode switching logic."""
import pytest
from cogency.nodes.reasoning.adaptation import parse_switch, should_switch, switch_mode, switch_prompt


class TestModeSwitch:
    """Test mode switch extraction from LLM responses."""
    
    @pytest.mark.parametrize("response,expected_mode,expected_reason", [
        (
            '''This task requires deeper analysis than I thought.
            {"switch_to": "deep", "switch_reason": "complex synthesis needed"}''',
            "deep", 
            "complex synthesis needed"
        ),
        (
            '''Actually this is just a simple lookup.
            {"switch_to": "fast", "switch_reason": "simpler than expected"}''',
            "fast",
            "simpler than expected"
        ),
        (
            '''I'll continue with the current approach.
            {"reasoning": "making progress with current strategy"}''',
            None,
            None
        ),
        (
            '''{"switch_to": "deep", invalid json''',
            None,
            None
        )
    ])
    def test_extract_mode_switch(self, response, expected_mode, expected_reason):
        """Test extracting mode switch from various responses."""
        mode, reason = parse_switch(response)
        assert mode == expected_mode
        assert reason == expected_reason


class TestShouldSwitch:
    """Test mode switching decision logic."""
    
    @pytest.mark.parametrize("current_mode,switch_to,switch_reason,current_iteration,expected", [
        # Should switch cases
        ("fast", "deep", "needs complex analysis", 2, True),
        ("deep", "fast", "simpler than expected", 1, True),
        # Should not switch cases
        ("fast", "fast", "continue current approach", 1, False),
        ("fast", "deep", "needs analysis", 4, False)  # Late iteration
    ])
    def test_should_switch(self, current_mode, switch_to, switch_reason, current_iteration, expected):
        """Test mode switching decision logic with various scenarios."""
        result = should_switch(
            current_mode=current_mode,
            switch_to=switch_to,
            switch_reason=switch_reason,
            current_iteration=current_iteration
        )
        assert result is expected


class TestExecuteSwitch:
    """Test mode switch execution."""
    
    @pytest.mark.parametrize("initial_mode,new_mode,expected_history,expected_failures", [
        ("fast", "deep", 10, 15),
        ("deep", "fast", 3, 5)
    ])
    def test_execute_switch(self, initial_mode, new_mode, expected_history, expected_failures):
        """Test mode switching updates state correctly."""
        state = {
            'react_mode': initial_mode,
            'cognition': {
                'react_mode': initial_mode,
                'max_history': 10 if initial_mode == "deep" else 3,
                'max_failures': 15 if initial_mode == "deep" else 5
            }
        }
        
        updated_state = switch_mode(
            state, 
            new_mode=new_mode,
            switch_reason=f"switching to {new_mode} mode"
        )
        
        assert updated_state['react_mode'] == new_mode
        assert updated_state['cognition']['react_mode'] == new_mode
        assert updated_state['cognition']['max_history'] == expected_history
        assert updated_state['cognition']['max_failures'] == expected_failures


class TestPromptAddition:
    """Test mode switch prompt additions."""
    
    @pytest.mark.parametrize("mode,expected_words", [
        ("fast", ["deep", ["complex", "analysis"]]),
        ("deep", ["fast", ["simple", "efficient"]])
    ])
    def test_prompt_addition(self, mode, expected_words):
        """Test prompt additions for different modes."""
        addition = switch_prompt(mode)
        
        # Check for the target mode in the prompt
        assert expected_words[0] in addition.lower()
        
        # Check for at least one of the expected descriptive words
        assert any(word in addition.lower() for word in expected_words[1])