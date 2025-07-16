import pytest
from unittest.mock import patch, MagicMock
from cogency.utils.tracing import Tracer
from cogency.common.types import ExecutionTrace

@pytest.fixture
def trace():
    t = ExecutionTrace()
    t.add("think", "Thinking about the problem")
    t.add("plan", "Selected tools for the job")
    t.add("act", "Executed tool A")
    t.add("reflect", "Generated final answer")
    return t

@pytest.fixture
def tracer(trace):
    return Tracer(trace)

def test_tracer_summarize(tracer):
    """Test that the tracer generates a correct summary."""
    summary = tracer._summarize()
    assert summary == "Selected tools for the job → Executed tool A → Generated final answer"

def test_tracer_format_trace(tracer):
    """Test that the tracer formats the trace correctly."""
    formatted_trace = tracer._format_trace()
    assert "🤔 THINK" in formatted_trace
    assert "🧠 PLAN" in formatted_trace
    assert "⚡ ACT" in formatted_trace
    assert "🔍 REFLECT" in formatted_trace

@patch('builtins.print')
def test_tracer_output_summary(mock_print, tracer):
    """Test the summary output mode."""
    tracer.output("summary")
    mock_print.assert_called_once_with("✅ Selected tools for the job → Executed tool A → Generated final answer")

@patch('builtins.print')
def test_tracer_output_trace(mock_print, tracer):
    """Test the trace output mode."""
    tracer.output("trace")
    # We can't easily test the full output, so we'll just check the last call
    mock_print.assert_called_with("\n✅ Complete")