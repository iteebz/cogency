import pytest
from cogency.common.types import ExecutionTrace, summarize_trace, format_trace

@pytest.fixture
def trace():
    return ExecutionTrace()

def test_execution_trace_add(trace):
    """Test that entries are added to the trace correctly."""
    trace.add("think", "Thinking about the problem")
    trace.add("plan", "Making a plan", {"steps": ["step1", "step2"]})
    assert len(trace.entries) == 2
    assert trace.entries[0]["node"] == "think"
    assert trace.entries[1]["data"] == {"steps": ["step1", "step2"]}

def test_summarize_trace(trace):
    """Test that the trace summary is generated correctly."""
    trace.add("think", "Thinking about the problem")
    trace.add("plan", "Selected tools for the job")
    trace.add("act", "Executed tool A")
    trace.add("reflect", "Generated final answer")
    summary = summarize_trace(trace)
    assert summary == "Selected tools for the job → Executed tool A → Generated final answer"

def test_format_trace(trace):
    """Test that the trace is formatted correctly."""
    trace.add("think", "Thinking about the problem")
    trace.add("plan", "Making a plan")
    formatted_trace = format_trace(trace)
    assert "🤔 THINK" in formatted_trace
    assert "🧠 PLAN" in formatted_trace

def test_summarize_trace_no_keywords(trace):
    """Test that a default message is returned when no keywords are found."""
    trace.add("think", "Mulling it over")
    trace.add("plan", "Devising a strategy")
    summary = summarize_trace(trace)
    assert summary == "Task completed"