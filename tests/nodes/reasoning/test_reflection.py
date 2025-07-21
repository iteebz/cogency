"""Tests for UltraThink reflection phases."""
import pytest
from cogency.nodes.reasoning.reflection import reflection_prompt, reflection, format_reflection, needs_reflection


class TestDeepReflectionPrompt:
    """Test deep reflection prompt generation."""
    
    def test_prompt_structure(self):
        """Test reflection prompt has proper UltraThink structure."""
        prompt = reflection_prompt(
            tool_info="search: Find information",
            query="What is the capital of France?",
            current_iteration=2,
            max_iterations=5,
            current_strategy="search_approach",
            previous_attempts="searched for France capital",
            last_tool_quality="good"
        )
        
        # Check for UltraThink phases
        assert "🤔 REFLECTION PHASE:" in prompt
        assert "📋 PLANNING PHASE:" in prompt  
        assert "🎯 EXECUTION PHASE:" in prompt
        
        # Check input data is included
        assert "What is the capital of France?" in prompt
        assert "search: Find information" in prompt
        assert "2/5" in prompt
    
    def test_mode_switching_in_prompt(self):
        """Test prompt includes mode switching capability."""
        prompt = reflection_prompt(
            "tools", "query", 1, 5, "strategy", "attempts", "quality"
        )
        
        assert "switch_to" in prompt
        assert "fast" in prompt
        assert "COGNITIVE ADJUSTMENT" in prompt


class TestExtractReflectionPhases:
    """Test reflection phase extraction from LLM responses."""
    
    def test_extract_json_phases(self):
        """Test extracting phases from proper JSON response."""
        response = '''Let me reflect on this task.
        
        {
          "reflection": "I've learned that this requires search first",
          "planning": "I'll search for information then analyze", 
          "execution_reasoning": "Starting with a targeted search",
          "strategy": "search_then_analyze"
        }'''
        
        phases = reflection(response)
        assert phases['reflection'] == "I've learned that this requires search first"
        assert phases['planning'] == "I'll search for information then analyze"
        assert phases['execution_reasoning'] == "Starting with a targeted search"
        assert phases['strategy'] == "search_then_analyze"
    
    def test_extract_text_phases(self):
        """Test extracting phases from text-based response."""
        response = '''🤔 REFLECTION PHASE:
        I can see this task needs more analysis than I initially thought.
        
        📋 PLANNING PHASE:
        My strategy will be to search first then synthesize the results.
        
        🎯 EXECUTION PHASE:
        I'll start with a comprehensive search.'''
        
        phases = reflection(response)
        assert "more analysis than I initially thought" in phases['reflection']
        assert phases['strategy'] == 'extracted_from_text'
    
    def test_extract_no_phases(self):
        """Test graceful handling when no phases found."""
        response = '''I'll just proceed with the search directly.'''
        
        phases = reflection(response)
        assert phases['reflection'] is None
        assert phases['planning'] is None
        assert phases['execution_reasoning'] is None


class TestFormatReflectionDisplay:
    """Test reflection formatting for display."""
    
    def test_format_all_phases(self):
        """Test formatting when all phases present."""
        phases = {
            'reflection': 'This requires deeper analysis',
            'planning': 'Search first then synthesize', 
            'execution_reasoning': 'Starting with targeted search'
        }
        
        display = format_reflection(phases)
        
        assert '🤔 REFLECTION:' in display
        assert '📋 PLANNING:' in display
        assert '🎯 EXECUTION:' in display
        assert 'This requires deeper analysis' in display
    
    def test_format_partial_phases(self):
        """Test formatting with only some phases.""" 
        phases = {
            'reflection': 'Task needs more work',
            'planning': None,
            'execution_reasoning': None
        }
        
        display = format_reflection(phases)
        
        assert '🤔 REFLECTION:' in display
        assert '📋 PLANNING:' not in display
        assert 'Task needs more work' in display
    
    def test_format_empty_phases(self):
        """Test fallback formatting when no phases."""
        phases = {}
        
        display = format_reflection(phases)
        assert display == "Thinking through the problem..."


class TestShouldUseReflection:
    """Test reflection usage decision logic."""
    
    def test_use_reflection_deep_mode(self):
        """Test reflection is used in deep mode."""
        should_use = needs_reflection("deep", 1)
        assert should_use is True
    
    def test_no_reflection_fast_mode(self):
        """Test reflection is not used in fast mode."""
        should_use = needs_reflection("fast", 1) 
        assert should_use is False
    
    def test_reflection_all_iterations_deep(self):
        """Test reflection used across all iterations in deep mode."""
        should_use = needs_reflection("deep", 3)
        assert should_use is True