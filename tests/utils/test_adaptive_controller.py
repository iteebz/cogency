#!/usr/bin/env python3
"""Tests for adaptive reasoning controller metrics and tracking."""

import asyncio
from cogency.utils.adaptive_reasoning import AdaptiveReasoningController, StoppingCriteria


class TestControllerInitialization:
    """Tests for controller initialization."""
    
    def test_initialization(self):
        """Test controller initialization."""
        controller = AdaptiveReasoningController()
        
        assert controller.criteria is not None
        assert controller.metrics is not None
        assert controller.iteration_history == []
        assert controller.consecutive_errors == 0
    
    def test_start_reasoning(self):
        """Test reasoning session initialization."""
        controller = AdaptiveReasoningController()
        import time
        start_time = time.time()
        
        controller.start_reasoning()
        
        assert controller.metrics.iteration == 0
        assert controller.metrics.start_time >= start_time
        assert controller.metrics.total_tools_executed == 0
        assert controller.iteration_history == []
        assert controller.consecutive_errors == 0


class TestMetricsTracking:
    """Tests for metrics tracking and updates."""
    
    def test_update_iteration_metrics(self):
        """Test iteration metrics updates."""
        controller = AdaptiveReasoningController()
        controller.start_reasoning()
        
        execution_results = {
            "total_executed": 3,
            "successful_count": 2,
            "failed_count": 1,
            "success": True,
            "results": [
                {"tool_name": "tool1", "result": "result1"},
                {"tool_name": "tool2", "result": "result2"}
            ]
        }
        
        controller.update_iteration_metrics(execution_results, 0.5)
        
        assert controller.metrics.iteration == 1
        assert controller.metrics.total_tools_executed == 3
        assert controller.metrics.successful_tools == 2
        assert controller.metrics.failed_tools == 1
        assert len(controller.metrics.execution_times) == 1
        assert len(controller.metrics.confidence_scores) == 1
        assert len(controller.iteration_history) == 1
    
    def test_consecutive_error_tracking(self):
        """Test consecutive error tracking."""
        controller = AdaptiveReasoningController()
        controller.start_reasoning()
        
        # Simulate failed execution
        failed_execution = {
            "total_executed": 2,
            "successful_count": 0,
            "failed_count": 2,
            "success": False
        }
        
        controller.update_iteration_metrics(failed_execution, 0.5)
        assert controller.consecutive_errors == 1
        
        # Another failed execution
        controller.update_iteration_metrics(failed_execution, 0.5)
        assert controller.consecutive_errors == 2
        
        # Successful execution should reset counter
        successful_execution = {
            "total_executed": 1,
            "successful_count": 1,
            "failed_count": 0,
            "success": True
        }
        
        controller.update_iteration_metrics(successful_execution, 0.5)
        assert controller.consecutive_errors == 0
    
    def test_confidence_score_calculation(self):
        """Test confidence score calculation."""
        controller = AdaptiveReasoningController()
        controller.start_reasoning()
        
        # High success rate with substantial results
        execution_results = {
            "total_executed": 3,
            "successful_count": 3,
            "failed_count": 0,
            "success": True,
            "results": [
                {"tool_name": "tool1", "result": "x" * 100},  # Substantial result
                {"tool_name": "tool2", "result": "y" * 100},
                {"tool_name": "tool3", "result": "z" * 100}
            ]
        }
        
        confidence = controller._calculate_confidence_score(execution_results, 1.0)
        
        # Should be high confidence due to perfect success rate and substantial results
        assert confidence > 0.8
        assert confidence <= 1.0


class TestSummaryAndReporting:
    """Tests for summary generation and reporting."""
    
    def test_reasoning_summary(self):
        """Test reasoning session summary."""
        controller = AdaptiveReasoningController()
        controller.start_reasoning()
        
        # Simulate some activity
        controller.metrics.iteration = 3
        controller.metrics.total_tools_executed = 5
        controller.metrics.successful_tools = 4
        controller.metrics.failed_tools = 1
        controller.metrics.confidence_scores = [0.8, 0.9, 0.85]
        controller.metrics.execution_times = [0.1, 0.2, 0.15]
        
        summary = controller.get_reasoning_summary()
        
        assert summary["total_iterations"] == 3
        assert summary["total_tools_executed"] == 5
        assert summary["success_rate"] == 0.8
        assert summary["avg_confidence"] == 0.85
        assert summary["avg_iteration_time"] == 0.15
        assert summary["consecutive_errors"] == 0
        assert "iteration_history" in summary
    
    def test_trace_log_generation(self):
        """Test trace log generation."""
        controller = AdaptiveReasoningController()
        controller.start_reasoning()
        
        # Add some iteration history
        controller.iteration_history = [
            {"iteration": 1, "time": 0.1, "tools_executed": 2, "success_rate": 1.0, "confidence": 0.8}
        ]
        
        trace_log = controller.get_trace_log()
        
        assert len(trace_log) >= 1
        assert trace_log[0]["event"] == "reasoning_started"
        assert "criteria" in trace_log[0]
        
        if len(trace_log) > 1:
            assert trace_log[1]["event"] == "iteration_completed"
            assert "iteration" in trace_log[1]
            assert "confidence" in trace_log[1]
    
    def test_adaptive_max_iterations(self):
        """Test adaptive max iterations calculation."""
        controller = AdaptiveReasoningController()
        
        # Low complexity should get fewer iterations
        low_complexity_iterations = controller.get_adaptive_max_iterations(0.2)
        assert low_complexity_iterations >= 2
        
        # High complexity should get more iterations
        high_complexity_iterations = controller.get_adaptive_max_iterations(0.9)
        assert high_complexity_iterations > low_complexity_iterations
        assert high_complexity_iterations <= 8  # Should be capped


async def run_controller_metrics_tests():
    """Run controller metrics tests."""
    print("📊 Testing controller metrics...")
    
    # Initialization tests
    init_tests = TestControllerInitialization()
    init_tests.test_initialization()
    print("✅ Controller initialization")
    
    init_tests.test_start_reasoning()
    print("✅ Reasoning session start")
    
    # Metrics tracking tests
    metrics_tests = TestMetricsTracking()
    metrics_tests.test_update_iteration_metrics()
    print("✅ Iteration metrics update")
    
    metrics_tests.test_consecutive_error_tracking()
    print("✅ Consecutive error tracking")
    
    metrics_tests.test_confidence_score_calculation()
    print("✅ Confidence score calculation")
    
    # Summary and reporting tests
    summary_tests = TestSummaryAndReporting()
    summary_tests.test_reasoning_summary()
    print("✅ Reasoning summary generation")
    
    summary_tests.test_trace_log_generation()
    print("✅ Trace log generation")
    
    summary_tests.test_adaptive_max_iterations()
    print("✅ Adaptive max iterations")
    
    print("\n🎉 All controller metrics tests passed!")


if __name__ == "__main__":
    asyncio.run(run_controller_metrics_tests())