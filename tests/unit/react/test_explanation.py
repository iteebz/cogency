#!/usr/bin/env python3
"""Standalone test for explanation system without full cogency imports."""



from cogency.utils.explanation import ExplanationGenerator, ExplanationLevel, ExplanationContext, create_actionable_insights


def test_explanation_generator_basic():
    """Test basic explanation generation functionality."""
    print("🧪 Testing explanation generator basic functionality...")
    
    # Test concise explanations
    generator = ExplanationGenerator(ExplanationLevel.CONCISE)
    
    context = ExplanationContext(
        user_query="What is Python?",
        tools_available=["search", "web_scraper"],
        reasoning_depth=2,
        execution_time=1.5,
        success=True
    )
    
    # Test reasoning start explanation
    explanation = generator.explain_reasoning_start(context)
    assert "🤔" in explanation
    assert "simple" in explanation.lower()
    print("  ✅ Reasoning start explanation works")
    
    # Test tool selection explanation
    explanation = generator.explain_tool_selection(["search"], 5)
    assert "🔧" in explanation
    assert "search" in explanation
    print("  ✅ Tool selection explanation works")
    
    # Test reasoning decision explanation
    explanation = generator.explain_reasoning_decision("direct_response", "I can answer directly")
    assert "💡" in explanation
    assert "directly" in explanation.lower()
    print("  ✅ Reasoning decision explanation works")
    
    print("🎉 Basic explanation generator tests passed!")


def test_explanation_levels():
    """Test different explanation detail levels."""
    print("🧪 Testing explanation detail levels...")
    
    context = ExplanationContext(
        user_query="Analyze performance implications of different ML frameworks",
        tools_available=["search", "database", "calculator"],
        reasoning_depth=5,
        execution_time=8.2,
        success=True
    )
    
    # Test concise level
    concise_gen = ExplanationGenerator(ExplanationLevel.CONCISE)
    concise_explanation = concise_gen.explain_reasoning_start(context)
    
    # Test detailed level
    detailed_gen = ExplanationGenerator(ExplanationLevel.DETAILED)
    detailed_explanation = detailed_gen.explain_reasoning_start(context)
    
    # Test technical level
    technical_gen = ExplanationGenerator(ExplanationLevel.TECHNICAL)
    technical_explanation = technical_gen.explain_reasoning_start(context)
    
    # Verify different levels provide different content
    assert len(concise_explanation) < len(detailed_explanation)
    # Technical may be shorter but more precise, so just check they're different
    assert concise_explanation != detailed_explanation
    assert detailed_explanation != technical_explanation
    
    # Verify content appropriateness
    assert "complex" in concise_explanation.lower()
    assert "complex" in detailed_explanation.lower()
    assert "max_iterations" in technical_explanation.lower()
    
    print("  ✅ Explanation levels work correctly")
    print("🎉 Explanation levels tests passed!")


def test_stopping_criteria_explanations():
    """Test explanations for different stopping criteria."""
    print("🧪 Testing stopping criteria explanations...")
    
    generator = ExplanationGenerator(ExplanationLevel.CONCISE)
    metrics = {"total_iterations": 3, "total_time": 4.5}
    
    # Test different stopping reasons
    stopping_reasons = [
        "confidence_threshold",
        "time_limit", 
        "max_iterations",
        "diminishing_returns",
        "resource_limit",
        "task_complete"
    ]
    
    for reason in stopping_reasons:
        explanation = generator.explain_stopping_criteria(reason, metrics)
        assert "🏁" in explanation
        assert explanation is not None
        print(f"  ✅ {reason} explanation works")
    
    print("🎉 Stopping criteria explanation tests passed!")


def test_actionable_insights():
    """Test actionable insights generation."""
    print("🧪 Testing actionable insights generation...")
    
    # Create mock trace entries
    trace_entries = [
        {"node": "reason", "message": "Tool execution started", "timestamp": 1000},
        {"node": "reason", "message": "Tool execution completed", "timestamp": 1015},
        {"node": "select_tools", "message": "Selected tools", "timestamp": 1002},
    ]
    
    # Test slow execution context
    slow_context = ExplanationContext(
        user_query="Complex analysis task",
        tools_available=["tool1", "tool2", "tool3"],
        reasoning_depth=3,
        execution_time=12.0,  # Over 10 seconds
        success=True
    )
    
    insights = create_actionable_insights(trace_entries, slow_context)
    assert len(insights) > 0
    assert any("faster responses" in insight for insight in insights)
    print("  ✅ Slow execution insights work")
    
    # Test unsuccessful context
    fail_context = ExplanationContext(
        user_query="Some task",
        tools_available=["tool1"],
        reasoning_depth=2,
        execution_time=3.0,
        success=False
    )
    
    insights = create_actionable_insights(trace_entries, fail_context)
    assert any("partially completed" in insight for insight in insights)
    print("  ✅ Failure insights work")
    
    print("🎉 Actionable insights tests passed!")


