#!/usr/bin/env python3
"""Standalone test for tracer integration without full imports."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

from cogency.types import ExecutionTrace
from cogency.tracer import Tracer


def test_tracer_basic_modes():
    """Test basic tracer modes work."""
    print("🧪 Testing basic tracer modes...")
    
    # Create simple trace
    trace = ExecutionTrace()
    trace.add("reason", "Simple test message")
    
    tracer = Tracer(trace)
    
    # Test summary mode
    summary = tracer._summarize()
    assert summary is not None
    print("  ✅ Summary mode works")
    
    # Test trace mode
    trace_output = tracer._format_trace()
    assert "REASON" in trace_output
    print("  ✅ Trace mode works")
    
    print("🎉 Basic tracer modes tests passed!")


def test_tracer_explained_mode():
    """Test tracer explained mode."""
    print("🧪 Testing tracer explained mode...")
    
    # Create trace with explanation
    trace = ExecutionTrace()
    trace.add("reason", "Adaptive reasoning started", explanation="🤔 Starting to think through your request")
    trace.add("reason", "Direct response generated", explanation="💡 I can answer this directly")
    
    tracer = Tracer(trace)
    
    # Test explained trace format
    explained_output = tracer._format_explained_trace()
    assert "🤔" in explained_output
    assert "💡" in explained_output
    print("  ✅ Explained trace format works")
    
    print("🎉 Tracer explained mode tests passed!")


def test_tracer_context_extraction():
    """Test tracer context extraction."""
    print("🧪 Testing tracer context extraction...")
    
    # Create trace with data
    trace = ExecutionTrace()
    trace.add("memorize", "Memory initialized", data={"query": "Test query"})
    trace.add("select_tools", "Tools selected", data={"selected_tools": [{"name": "search"}]})
    trace.add("reason", "Adaptive reasoning started - complexity: 0.5, max_iterations: 3")
    
    tracer = Tracer(trace)
    
    # Test context building
    context = tracer._build_explanation_context()
    assert "Test query" in context.user_query
    assert "search" in context.tools_available
    assert context.reasoning_depth == 3
    print("  ✅ Context extraction works")
    
    print("🎉 Tracer context extraction tests passed!")


def test_tracer_explanation_generation():
    """Test tracer explanation generation."""
    print("🧪 Testing tracer explanation generation...")
    
    trace = ExecutionTrace()
    tracer = Tracer(trace)
    
    # Mock context
    from cogency.utils.explanation import ExplanationContext
    context = ExplanationContext(
        user_query="Test query",
        tools_available=["search"],
        reasoning_depth=2,
        execution_time=1.0,
        success=True
    )
    
    # Test different entry types
    test_cases = [
        ({"node": "memorize", "message": "Memory recalled", "data": {}}, "🧠"),
        ({"node": "select_tools", "message": "Tools selected", "data": {"selected_tools": [{"name": "search"}]}}, "🔧"),
        ({"node": "reason", "message": "Adaptive reasoning started", "data": {}}, "🤔"),
        ({"node": "reason", "message": "Direct response generated", "data": {}}, "💡"),
    ]
    
    for entry, expected_emoji in test_cases:
        explanation = tracer._generate_explanation_for_entry(entry, context)
        if explanation:
            assert expected_emoji in explanation
            print(f"  ✅ {entry['node']} explanation works")
    
    print("🎉 Tracer explanation generation tests passed!")


if __name__ == "__main__":
    test_tracer_basic_modes()
    test_tracer_explained_mode()
    test_tracer_context_extraction()
    test_tracer_explanation_generation()
    print("\n🎉 All standalone tracer tests passed!")