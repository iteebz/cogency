#!/usr/bin/env python3
"""Tests for stopping criteria configuration."""

import asyncio
import time
from cogency.react.adaptive_reasoning import (
    AdaptiveReasoningController, 
    StoppingCriteria, 
    StoppingReason
)


class TestStoppingCriteria:
    """Tests for stopping criteria configuration."""
    
    def test_default_criteria(self):
        """Test default stopping criteria values."""
        criteria = StoppingCriteria()
        
        assert criteria.confidence_threshold == 0.85
        assert criteria.max_reasoning_time == 30.0
        assert criteria.max_iterations == 5
        assert criteria.max_total_tools == 25
        assert criteria.improvement_threshold == 0.1
        assert criteria.stagnation_iterations == 2
    
    def test_custom_criteria(self):
        """Test custom stopping criteria configuration."""
        criteria = StoppingCriteria(
            confidence_threshold=0.9,
            max_reasoning_time=60.0,
            max_iterations=10,
            max_total_tools=50
        )
        
        assert criteria.confidence_threshold == 0.9
        assert criteria.max_reasoning_time == 60.0
        assert criteria.max_iterations == 10
        assert criteria.max_total_tools == 50


class TestBasicStoppingConditions:
    """Tests for basic stopping conditions."""
    
    def test_time_limit_stopping(self):
        """Test stopping due to time limits."""
        criteria = StoppingCriteria(max_reasoning_time=0.1)  # 100ms limit
        controller = AdaptiveReasoningController(criteria)
        controller.start_reasoning()
        
        # Wait longer than time limit
        time.sleep(0.2)
        
        should_continue, stopping_reason = controller.should_continue_reasoning()
        
        assert not should_continue
        assert stopping_reason == StoppingReason.TIME_LIMIT
    
    def test_iteration_limit_stopping(self):
        """Test stopping due to iteration limits."""
        criteria = StoppingCriteria(max_iterations=3)
        controller = AdaptiveReasoningController(criteria)
        controller.start_reasoning()
        
        # Simulate multiple iterations
        for i in range(3):
            controller.metrics.iteration = i + 1
            
        should_continue, stopping_reason = controller.should_continue_reasoning()
        
        assert not should_continue
        assert stopping_reason == StoppingReason.MAX_ITERATIONS
    
    def test_resource_limit_stopping(self):
        """Test stopping due to resource limits."""
        criteria = StoppingCriteria(max_total_tools=5)
        controller = AdaptiveReasoningController(criteria)
        controller.start_reasoning()
        
        # Simulate tool execution
        controller.metrics.total_tools_executed = 6
        
        should_continue, stopping_reason = controller.should_continue_reasoning()
        
        assert not should_continue
        assert stopping_reason == StoppingReason.RESOURCE_LIMIT
    
    def test_error_threshold_stopping(self):
        """Test stopping due to error thresholds."""
        criteria = StoppingCriteria(max_consecutive_errors=2)
        controller = AdaptiveReasoningController(criteria)
        controller.start_reasoning()
        
        # Simulate consecutive errors
        controller.consecutive_errors = 3
        
        should_continue, stopping_reason = controller.should_continue_reasoning()
        
        assert not should_continue
        assert stopping_reason == StoppingReason.ERROR_THRESHOLD


class TestAdvancedStoppingConditions:
    """Tests for advanced stopping conditions."""
    
    def test_confidence_threshold_stopping(self):
        """Test stopping due to confidence threshold."""
        criteria = StoppingCriteria(confidence_threshold=0.8, min_confidence_samples=2)
        controller = AdaptiveReasoningController(criteria)
        controller.start_reasoning()
        
        # Simulate high confidence scores
        controller.metrics.confidence_scores = [0.85, 0.9, 0.85]
        
        # Pass execution results to trigger confidence checking
        execution_results = {
            "success": True,
            "results": [{"tool_name": "tool1", "result": "good result"}],
            "total_executed": 1,
            "successful_count": 1,
            "failed_count": 0
        }
        
        should_continue, stopping_reason = controller.should_continue_reasoning(execution_results)
        
        assert not should_continue
        assert stopping_reason == StoppingReason.CONFIDENCE_THRESHOLD
    
    def test_diminishing_returns_detection(self):
        """Test diminishing returns detection."""
        criteria = StoppingCriteria(improvement_threshold=0.1, stagnation_iterations=2)
        controller = AdaptiveReasoningController(criteria)
        controller.start_reasoning()
        
        # Simulate stagnant confidence scores
        controller.iteration_history = [
            {"iteration": 1, "confidence": 0.7, "time": 0.1, "tools_executed": 1, "success_rate": 1.0},
            {"iteration": 2, "confidence": 0.71, "time": 0.1, "tools_executed": 1, "success_rate": 1.0},
            {"iteration": 3, "confidence": 0.72, "time": 0.1, "tools_executed": 1, "success_rate": 1.0}
        ]
        
        should_continue, stopping_reason = controller.should_continue_reasoning()
        
        assert not should_continue
        assert stopping_reason == StoppingReason.DIMINISHING_RETURNS


