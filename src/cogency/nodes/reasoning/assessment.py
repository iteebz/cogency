"""Tool execution quality assessment."""
from typing import Dict, Any


def assess_tool_quality(execution_results: Dict[str, Any]) -> str:
    """Assess quality of tool execution results."""
    if not execution_results:
        return "unknown"
    
    # Check if execution was successful
    if not execution_results.get("success", False):
        return "failed"
    
    # Check result quality indicators
    results = execution_results.get("results", [])
    if not results:
        return "poor"
    
    # Simple heuristics for result quality
    successful_count = execution_results.get("successful_count", 0)
    failed_count = execution_results.get("failed_count", 0)
    total_count = successful_count + failed_count
    
    if total_count == 0:
        return "unknown"
    
    success_rate = successful_count / total_count
    
    if success_rate >= 0.8:
        return "good"
    elif success_rate >= 0.5:
        return "partial"
    else:
        return "poor"