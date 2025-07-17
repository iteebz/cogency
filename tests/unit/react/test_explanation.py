"""Pragmatic tests for explanation - core explanation generation."""
import pytest
from cogency.react.explanation import ExplanationGenerator, ExplanationLevel, ExplanationContext, create_actionable_insights


class TestExplanationGenerator:
    """Test core explanation generation logic."""

    def test_reasoning_start_explanations(self):
        """Test reasoning start explanations across levels."""
        context = ExplanationContext(
            user_query="Test query",
            tools_available=["search"],
            reasoning_depth=2,
            execution_time=1.0,
            success=True
        )

        # Test each level produces different output
        concise = ExplanationGenerator(ExplanationLevel.CONCISE)
        detailed = ExplanationGenerator(ExplanationLevel.DETAILED)
        technical = ExplanationGenerator(ExplanationLevel.TECHNICAL)

        concise_exp = concise.explain_reasoning_start(context)
        detailed_exp = detailed.explain_reasoning_start(context)
        technical_exp = technical.explain_reasoning_start(context)

        # All should contain emoji and be different
        assert "🤔" in concise_exp
        assert "🤔" in detailed_exp
        assert "🤔" in technical_exp
        assert concise_exp != detailed_exp != technical_exp

    def test_tool_selection_explanations(self):
        """Test tool selection explanations."""
        generator = ExplanationGenerator(ExplanationLevel.CONCISE)

        # No tools case
        no_tools = generator.explain_tool_selection([], 0)
        assert "No tools needed" in no_tools

        # With tools case
        with_tools = generator.explain_tool_selection(["search", "calculator"], 5)
        assert "🔧" in with_tools
        assert "search" in with_tools
        assert "calculator" in with_tools

    def test_stopping_criteria_explanations(self):
        """Test stopping criteria explanations."""
        generator = ExplanationGenerator(ExplanationLevel.CONCISE)
        metrics = {"total_iterations": 3, "total_time": 4.5}

        # Test key stopping reasons
        for reason in ["confidence_threshold", "time_limit", "max_iterations"]:
            explanation = generator.explain_stopping_criteria(reason, metrics)
            assert "🏁" in explanation
            assert explanation is not None

    def test_actionable_insights(self):
        """Test actionable insights generation."""
        trace_entries = [
            {"node": "reason", "message": "Tool execution", "timestamp": 1000}
        ]

        # Test slow execution insight
        slow_context = ExplanationContext(
            user_query="Complex task",
            tools_available=["tool1"],
            reasoning_depth=3,
            execution_time=12.0,  # Over 10 seconds
            success=True
        )

        insights = create_actionable_insights(trace_entries, slow_context)
        assert len(insights) > 0
        assert any("faster responses" in insight for insight in insights)

        # Test failure insight
        fail_context = ExplanationContext(
            user_query="Some task",
            tools_available=["tool1"],
            reasoning_depth=2,
            execution_time=3.0,
            success=False
        )

        insights = create_actionable_insights(trace_entries, fail_context)
        assert any("partially completed" in insight for insight in insights)