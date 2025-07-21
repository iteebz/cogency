"""Tests for UltraThink planning capabilities."""
import pytest
from cogency.nodes.reasoning.planning import extract_planning_strategy, validate_planning_quality, create_multi_step_plan, format_plan_for_display


class TestExtractPlanningStrategy:
    """Test planning strategy extraction."""
    
    def test_extract_json_planning(self):
        """Test extracting planning from JSON response."""
        response = '''Let me plan this approach.
        
        {
          "strategy": "search_and_analyze",
          "planning": "First search for data, then analyze patterns", 
          "approach": "methodical_research",
          "tool_sequence": ["search", "analyze"],
          "expected_obstacles": ["data quality", "time constraints"]
        }'''
        
        planning = extract_planning_strategy(response)
        
        assert planning['strategy'] == "search_and_analyze"
        assert planning['planning'] == "First search for data, then analyze patterns"
        assert planning['approach'] == "methodical_research"
        assert planning['tool_sequence'] == ["search", "analyze"]
        assert planning['expected_obstacles'] == ["data quality", "time constraints"]
    
    def test_extract_text_planning(self):
        """Test extracting planning from text response."""
        response = '''📋 PLANNING PHASE:
        I need to break this down into steps. First I'll search for information,
        then I'll analyze the results and synthesize findings.
        
        🎯 EXECUTION PHASE:
        Starting with comprehensive search.'''
        
        planning = extract_planning_strategy(response)
        
        assert planning['strategy'] == 'text_extracted'
        assert 'break this down into steps' in planning['planning']
        assert 'search for information' in planning['planning']
    
    def test_extract_no_planning(self):
        """Test when no planning is found."""
        response = '''I'll just proceed with the direct approach.'''
        
        planning = extract_planning_strategy(response)
        assert planning is None


class TestValidatePlanningQuality:
    """Test planning quality validation."""
    
    def test_valid_planning_quality(self):
        """Test recognizing high-quality planning."""
        planning = {
            'planning': 'First I need to search for information because the query requires research. Then I will analyze the results and synthesize findings.'
        }
        
        is_valid = validate_planning_quality(planning)
        assert is_valid is True
    
    def test_low_quality_planning(self):
        """Test rejecting low-quality planning."""
        planning = {
            'planning': 'Do it.'  # Too short, no strategy words
        }
        
        is_valid = validate_planning_quality(planning)
        assert is_valid is False
    
    def test_empty_planning(self):
        """Test handling empty planning."""
        planning = None
        
        is_valid = validate_planning_quality(planning)
        assert is_valid is False
    
    def test_planning_quality_indicators(self):
        """Test quality indicators are recognized.""" 
        planning = {
            'planning': 'My approach will be to first search, then analyze because this needs careful strategy.'
        }
        
        is_valid = validate_planning_quality(planning)
        assert is_valid is True  # Has 'approach', 'first', 'then', 'because', 'strategy'


class TestCreateMultiStepPlan:
    """Test multi-step plan creation."""
    
    def test_search_query_plan(self):
        """Test plan creation for search queries."""
        plan = create_multi_step_plan(
            "Find information about machine learning",
            ["search", "analyze"], 
            None
        )
        
        assert plan['total_steps'] >= 1
        assert any(step['action'] == 'search' for step in plan['steps'])
        assert plan['complexity'] in ['medium', 'high']
    
    def test_analysis_query_plan(self):
        """Test plan creation for analysis queries."""
        plan = create_multi_step_plan(
            "Analyze and compare different ML algorithms",
            ["search", "code"],
            None
        )
        
        assert plan['total_steps'] >= 2  # Should have multiple steps for analysis
        assert any(step['action'] == 'gather_information' for step in plan['steps'])
        assert any(step['action'] == 'analyze' for step in plan['steps'])
    
    def test_simple_query_plan(self):
        """Test plan creation for simple queries."""
        plan = create_multi_step_plan(
            "What's the weather?", 
            ["weather"],
            None
        )
        
        # Simple queries should have minimal steps
        assert plan['total_steps'] <= 2
    
    def test_no_tools_plan(self):
        """Test plan creation with no tools."""
        plan = create_multi_step_plan(
            "Explain machine learning",
            [],
            None
        )
        
        assert plan['total_steps'] == 0
        assert plan['steps'] == []


class TestFormatPlanDisplay:
    """Test plan formatting for display."""
    
    def test_format_multi_step_plan(self):
        """Test formatting a multi-step plan."""
        plan = {
            'total_steps': 2,
            'steps': [
                {
                    'step': 1,
                    'action': 'search',
                    'reasoning': 'Gather initial information',
                    'tool': 'search'
                },
                {
                    'step': 2, 
                    'action': 'analyze',
                    'reasoning': 'Process the results',
                    'tool': 'reasoning'
                }
            ]
        }
        
        display = format_plan_for_display(plan)
        
        assert '📋 MULTI-STEP PLAN (2 steps):' in display
        assert '1. search - Gather initial information' in display
        assert '2. analyze - Process the results' in display
    
    def test_format_empty_plan(self):
        """Test formatting empty or simple plan."""
        plan = {'steps': []}
        
        display = format_plan_for_display(plan)
        assert display == "Simple direct approach"
    
    def test_format_none_plan(self):
        """Test formatting None plan."""
        display = format_plan_for_display(None)
        assert display == "Simple direct approach"