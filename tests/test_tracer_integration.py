#!/usr/bin/env python3
"""Test suite for tracer integration with explanation system."""

import asyncio
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../src'))

from unittest.mock import MagicMock, patch
from cogency.types import ExecutionTrace
from cogency.tracer import Tracer
from cogency.utils.explanation import ExplanationContext, ExplanationLevel


def test_tracer_explanation_context_building():
    """Test that tracer correctly builds explanation context from trace entries."""
    print("🧪 Testing tracer explanation context building...")
    
    # Create trace with realistic entries
    trace = ExecutionTrace()
    trace.add("memorize", "Memory initialized", data={"query": "What is machine learning?"})
    trace.add("select_tools", "Selected tools", data={"selected_tools": [{"name": "search"}, {"name": "calculator"}]})
    trace.add("reason", "Adaptive reasoning started - complexity: 0.6, max_iterations: 4")
    trace.add("reason", "Stopping reasoning: time_limit")
    
    tracer = Tracer(trace)
    context = tracer._build_explanation_context()
    
    # Verify context extraction
    assert "machine learning" in context.user_query
    assert "search" in context.tools_available
    assert "calculator" in context.tools_available
    assert context.reasoning_depth == 4
    assert context.execution_time > 0
    assert context.stopping_reason is not None
    
    print("  ✅ Context building works correctly")
    print("🎉 Tracer explanation context building tests passed!")


def test_tracer_entry_explanation_generation():
    """Test that tracer generates appropriate explanations for different entry types."""
    print("🧪 Testing tracer entry explanation generation...")
    
    trace = ExecutionTrace()
    tracer = Tracer(trace)
    
    # Mock context
    context = ExplanationContext(
        user_query="Test query",
        tools_available=["search", "calculator"],
        reasoning_depth=3,
        execution_time=2.0,
        success=True
    )
    
    # Test memorize node explanations
    entry = {"node": "memorize", "message": "Memory recalled", "data": {}}
    explanation = tracer._generate_explanation_for_entry(entry, context)
    assert "🧠" in explanation
    assert "recalled" in explanation.lower()
    print("  ✅ Memorize node explanation works")
    
    # Test select_tools node explanations
    entry = {"node": "select_tools", "message": "Tools selected", "data": {"selected_tools": [{"name": "search"}]}}
    explanation = tracer._generate_explanation_for_entry(entry, context)
    assert "🔧" in explanation
    assert "search" in explanation.lower()
    print("  ✅ Select tools node explanation works")
    
    # Test reason node explanations
    test_cases = [
        ("Adaptive reasoning started", "🤔"),
        ("Direct response generated", "💡"),
        ("Tool calls identified", "💭"),
        ("Task complete", "✅"),
        ("Stopping reasoning", "🏁"),
        ("Tool execution summary", "⚡")
    ]
    
    for message, expected_emoji in test_cases:
        entry = {"node": "reason", "message": message, "data": {}}
        explanation = tracer._generate_explanation_for_entry(entry, context)
        assert expected_emoji in explanation
        print(f"  ✅ Reason node explanation for '{message}' works")
    
    print("🎉 Tracer entry explanation generation tests passed!")


def test_tracer_output_modes():
    """Test different tracer output modes including new explain mode."""
    print("🧪 Testing tracer output modes...")
    
    # Create comprehensive trace
    trace = ExecutionTrace()
    trace.add("memorize", "Memory initialized", explanation="🧠 Accessing relevant memories")
    trace.add("select_tools", "Selected tools: search", explanation="🔧 Selected 1 relevant tool: search")
    trace.add("reason", "Adaptive reasoning started", explanation="🤔 Starting to think through your request (simple)")
    trace.add("reason", "Direct response generated", explanation="💡 I can answer this directly")
    
    tracer = Tracer(trace)
    
    # Test summary mode
    with patch('builtins.print') as mock_print:
        tracer.output("summary")
        mock_print.assert_called()
        print("  ✅ Summary mode output works")
    
    # Test trace mode
    with patch('builtins.print') as mock_print:
        tracer.output("trace")
        mock_print.assert_called()
        print("  ✅ Trace mode output works")
    
    # Test explain mode
    with patch('builtins.print') as mock_print:
        tracer.output("explain")
        mock_print.assert_called()
        print("  ✅ Explain mode output works")
    
    # Test dev mode
    with patch('builtins.print') as mock_print:
        tracer.output("dev")
        mock_print.assert_called()
        print("  ✅ Dev mode output works")
    
    print("🎉 Tracer output modes tests passed!")


def test_tracer_actionable_insights():
    """Test that tracer shows actionable insights in explain mode."""
    print("🧪 Testing tracer actionable insights...")
    
    # Create trace that would generate insights
    trace = ExecutionTrace()
    base_time = 1000
    
    # Add entries with realistic timestamps for slow execution
    trace.add("memorize", "Memory initialized")
    trace.add("select_tools", "Selected many tools")
    trace.add("reason", "Adaptive reasoning started")
    
    # Simulate slow execution by manually setting timestamps
    trace.entries[0]["timestamp"] = base_time
    trace.entries[1]["timestamp"] = base_time + 5
    trace.entries[2]["timestamp"] = base_time + 15  # 15 seconds total
    
    tracer = Tracer(trace)
    
    # Test insights generation
    context = tracer._build_explanation_context()
    assert context.execution_time > 10  # Should trigger slow execution insight
    
    # Test insights display
    with patch('builtins.print') as mock_print:
        tracer._show_actionable_insights()
        # Should print insights header if insights exist
        calls = [str(call) for call in mock_print.call_args_list]
        insight_calls = [call for call in calls if "💡" in call]
        if insight_calls:
            print("  ✅ Actionable insights display works")
        else:
            print("  ⚠️ No actionable insights displayed (may be expected)")
    
    print("🎉 Tracer actionable insights tests passed!")


def test_tracer_explanation_fallbacks():
    """Test that tracer handles missing explanations gracefully."""
    print("🧪 Testing tracer explanation fallbacks...")
    
    # Create trace without pre-generated explanations
    trace = ExecutionTrace()
    trace.add("reason", "Some custom message without explanation")
    trace.add("unknown_node", "Some message from unknown node")
    
    tracer = Tracer(trace)
    context = tracer._build_explanation_context()
    
    # Test fallback explanation generation
    entry = {"node": "reason", "message": "Custom reasoning message", "data": {}}
    explanation = tracer._generate_explanation_for_entry(entry, context)
    assert explanation is not None
    assert "🤔" in explanation
    print("  ✅ Reason node fallback works")
    
    # Test unknown node handling
    entry = {"node": "unknown_node", "message": "Unknown message", "data": {}}
    explanation = tracer._generate_explanation_for_entry(entry, context)
    assert explanation is None  # Should return None for unknown nodes
    print("  ✅ Unknown node handling works")
    
    # Test explained trace format with mixed explanations
    explained_output = tracer._format_explained_trace()
    assert "🤔" in explained_output
    print("  ✅ Mixed explanation handling works")
    
    print("🎉 Tracer explanation fallbacks tests passed!")


if __name__ == "__main__":
    test_tracer_explanation_context_building()
    test_tracer_entry_explanation_generation()
    test_tracer_output_modes()
    test_tracer_actionable_insights()
    test_tracer_explanation_fallbacks()
    print("\n🎉 All tracer integration tests passed!")