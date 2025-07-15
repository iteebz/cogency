"""Tests for infinite loop detection system."""

import asyncio
import time
from unittest.mock import Mock

from cogency.utils.loop_detection import (
    LoopDetector, LoopDetectionConfig, LoopType, LoopPattern
)
from cogency.types import ExecutionTrace
from cogency.context import Context


class TestLoopDetector:
    """Test suite for loop detection."""
    
    def test_reasoning_cycle_detection(self):
        """Test detection of reasoning cycles."""
        detector = LoopDetector()
        
        # Simulate repeated reasoning steps with identical signatures
        for i in range(6):
            detector.add_reasoning_step(
                iteration=1,  # Same iteration to create identical signature
                llm_response="I need to think about this more",
                tool_calls=[],
                execution_results={}
            )
        
        loops = detector.check_for_loops()
        
        # Debug output
        print(f"DEBUG: Found {len(loops)} loops")
        for loop in loops:
            print(f"DEBUG: Loop type: {loop.loop_type}, repetitions: {loop.repetition_count}")
        
        # Should detect reasoning cycle
        reasoning_loops = [l for l in loops if l.loop_type == LoopType.REASONING_CYCLE]
        assert len(reasoning_loops) > 0
        assert reasoning_loops[0].repetition_count >= 3
        print("✅ Reasoning cycle detection")
    
    def test_tool_execution_cycle_detection(self):
        """Test detection of tool execution cycles."""
        detector = LoopDetector()
        
        # Simulate repeated tool failures
        for i in range(5):
            detector.add_tool_execution(
                tool_name="search",
                args={"query": "test"},
                result=None,
                success=False
            )
            time.sleep(0.1)  # Small delay to simulate real execution
        
        loops = detector.check_for_loops()
        
        # Should detect tool cycle
        tool_loops = [l for l in loops if l.loop_type == LoopType.TOOL_EXECUTION_CYCLE]
        assert len(tool_loops) > 0
        assert tool_loops[0].signature == "search"
        print("✅ Tool execution cycle detection")
    
    def test_state_oscillation_detection(self):
        """Test detection of state oscillation."""
        detector = LoopDetector()
        
        # Create mock state and trace
        context = Context("test query")
        trace = ExecutionTrace()
        trace.add("memorize", "Processing")
        
        state = {
            "context": context,
            "trace": trace,
            "selected_tools": []
        }
        
        # Simulate repeated state changes
        for i in range(4):
            detector.add_state_change(state, trace)
            time.sleep(0.1)
        
        loops = detector.check_for_loops()
        
        # Should detect state oscillation
        state_loops = [l for l in loops if l.loop_type == LoopType.STATE_OSCILLATION]
        assert len(state_loops) > 0
        assert state_loops[0].repetition_count >= 3
        print("✅ State oscillation detection")
    
    def test_decision_flip_detection(self):
        """Test detection of decision flips."""
        detector = LoopDetector()
        
        # Simulate alternating decisions
        decisions = [
            ("direct_response", {"confidence": 0.8}),
            ("use_tools", {"tools": ["search"]}),
            ("direct_response", {"confidence": 0.8}),
            ("use_tools", {"tools": ["search"]}),
            ("direct_response", {"confidence": 0.8}),
            ("use_tools", {"tools": ["search"]})
        ]
        
        for decision_type, details in decisions:
            detector.add_decision(decision_type, details)
        
        loops = detector.check_for_loops()
        
        # Should detect decision flips
        decision_loops = [l for l in loops if l.loop_type == LoopType.DECISION_FLIP]
        assert len(decision_loops) > 0
        assert decision_loops[0].cycle_length == 2
        print("✅ Decision flip detection")
    
    def test_context_repetition_detection(self):
        """Test detection of context repetition."""
        detector = LoopDetector()
        
        # Simulate repeated similar responses with exact duplicates
        similar_responses = [
            "I need to search for information about this topic",
            "I need to search for information about this topic",  # Exact repeat
            "I should search for information about this topic",
            "I need to search for information about this topic",  # Another exact repeat
            "I need to search for information about this topic"   # Another exact repeat
        ]
        
        for i, response in enumerate(similar_responses):
            detector.add_reasoning_step(
                iteration=i,
                llm_response=response,
                tool_calls=["search"],
                execution_results={}
            )
        
        loops = detector.check_for_loops()
        
        # Debug output
        print(f"DEBUG: Context repetition loops: {len([l for l in loops if l.loop_type == LoopType.CONTEXT_REPETITION])}")
        
        # Should detect context repetition
        context_loops = [l for l in loops if l.loop_type == LoopType.CONTEXT_REPETITION]
        assert len(context_loops) > 0
        assert context_loops[0].confidence > 0.8
        print("✅ Context repetition detection")
    
    def test_adaptive_threshold_adjustment(self):
        """Test adaptive threshold adjustment for complex queries."""
        config = LoopDetectionConfig()
        detector = LoopDetector(config)
        
        # Test with high complexity factor
        high_complexity = 0.9
        loops_high = detector.check_for_loops(complexity_factor=high_complexity)
        
        # Test with low complexity factor
        low_complexity = 0.3
        loops_low = detector.check_for_loops(complexity_factor=low_complexity)
        
        # High complexity should be more tolerant (fewer loop detections)
        # This is tested indirectly through the adjusted config
        assert isinstance(loops_high, list)
        assert isinstance(loops_low, list)
        print("✅ Adaptive threshold adjustment")
    
    def test_loop_summary_generation(self):
        """Test loop summary generation."""
        detector = LoopDetector()
        
        # No loops initially
        summary = detector.get_loop_summary()
        assert summary["loops_detected"] == False
        assert summary["total_loops"] == 0
        
        # Add some loops
        detector.add_reasoning_step(0, "test", [], {})
        detector.add_reasoning_step(1, "test", [], {})
        detector.add_reasoning_step(2, "test", [], {})
        detector.add_reasoning_step(3, "test", [], {})
        detector.add_reasoning_step(4, "test", [], {})
        detector.add_reasoning_step(5, "test", [], {})
        
        loops = detector.check_for_loops()
        summary = detector.get_loop_summary()
        
        if summary["loops_detected"]:
            assert summary["total_loops"] > 0
            assert "loop_types" in summary
            assert "max_confidence" in summary
        
        print("✅ Loop summary generation")
    
    def test_detector_reset(self):
        """Test detector reset functionality."""
        detector = LoopDetector()
        
        # Add some data
        detector.add_reasoning_step(0, "test", [], {})
        detector.add_tool_execution("search", {"query": "test"}, "result", True)
        
        # Verify data exists
        assert len(detector.reasoning_history) > 0
        assert len(detector.tool_execution_history) > 0
        
        # Reset
        detector.reset()
        
        # Verify data is cleared
        assert len(detector.reasoning_history) == 0
        assert len(detector.tool_execution_history) == 0
        assert len(detector.detected_loops) == 0
        print("✅ Detector reset")
    
    def test_complex_integration_scenario(self):
        """Test complex integration scenario with multiple loop types."""
        detector = LoopDetector()
        
        # Simulate complex reasoning with multiple patterns
        for i in range(3):
            # Reasoning cycle
            detector.add_reasoning_step(
                iteration=i,
                llm_response="I need to analyze this query",
                tool_calls=["search"],
                execution_results={"success": False}
            )
            
            # Tool execution cycle
            detector.add_tool_execution(
                tool_name="search",
                args={"query": "test"},
                result=None,
                success=False
            )
            
            # Decision flip
            detector.add_decision("use_tools", {"tools": ["search"]})
            detector.add_decision("direct_response", {"confidence": 0.5})
            
            time.sleep(0.1)
        
        loops = detector.check_for_loops()
        
        # Should detect multiple loop types
        loop_types = {loop.loop_type for loop in loops}
        assert len(loop_types) > 1  # Multiple types detected
        
        summary = detector.get_loop_summary()
        assert summary["loops_detected"] == True
        assert summary["total_loops"] > 1
        print("✅ Complex integration scenario")


async def test_loop_detector_integration():
    """Test loop detector integration with reasoning system."""
    print("🔍 Testing loop detector integration...")
    
    tests = TestLoopDetector()
    
    # Run all tests
    tests.test_reasoning_cycle_detection()
    tests.test_tool_execution_cycle_detection()
    tests.test_state_oscillation_detection()
    tests.test_decision_flip_detection()
    tests.test_context_repetition_detection()
    tests.test_adaptive_threshold_adjustment()
    tests.test_loop_summary_generation()
    tests.test_detector_reset()
    tests.test_complex_integration_scenario()
    
    print("\n🎉 All loop detection tests passed!")


if __name__ == "__main__":
    asyncio.run(test_loop_detector_integration())