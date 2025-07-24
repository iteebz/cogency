"""Tool execution quality assessment."""

from typing import Optional

from cogency.utils.results import ExecutionResult


def assess_tools(execution_results: Optional[ExecutionResult]) -> str:
    """Assess tool execution with pragmatic heuristics - no semantic bullshit."""
    if execution_results is None:
        return "unknown"

    # Basic success/failure check
    if execution_results.failure:
        return "failed"

    # Check if we got any results at all
    results = execution_results.data.get("results", [])
    if not results:
        return "poor"

    # Simple success rate calculation
    successful_count = execution_results.data.get("successful_count", 0)
    failed_count = execution_results.data.get("failed_count", 0)
    total_count = successful_count + failed_count

    if total_count == 0:
        return "unknown"

    success_rate = successful_count / total_count

    # Basic technical success assessment - no content analysis
    if success_rate >= 0.8:
        return "good"
    elif success_rate >= 0.5:
        return "partial"
    else:
        return "poor"
