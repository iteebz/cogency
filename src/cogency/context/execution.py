"""Execution context - runtime execution state.

Runtime-only execution mechanics that are never persisted.
Handles tool calls, iterations, and execution flow.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Execution:
    """Runtime-only execution mechanics - NOT persisted."""
    
    iteration: int = 0
    max_iterations: int = 10
    stop_reason: str | None = None
    
    messages: list[dict[str, Any]] = field(default_factory=list)
    response: str | None = None
    
    pending_calls: list[dict[str, Any]] = field(default_factory=list)
    completed_calls: list[dict[str, Any]] = field(default_factory=list)
    iterations_without_tools: int = 0
    tool_results: dict[str, Any] = field(default_factory=dict)


class ExecutionContext:
    """Execution domain context - tool history and runtime state."""
    
    def __init__(self, execution: Execution):
        self.execution = execution
    
    async def build(self) -> str | None:
        """Build execution context from tool history and runtime state."""
        if not self.execution or not self.execution.completed_calls:
            return None
            
        parts = ["TOOL EXECUTION HISTORY:"]
        
        for call in self.execution.completed_calls[-3:]:  # Last 3 results
            tool_name = call.get("tool", "unknown")
            success = call.get("success", False)
            result = call.get("result", {})

            # Extract meaningful result summary
            summary = "completed"
            if hasattr(result, "get") and isinstance(result, dict):
                if result.get("result"):
                    summary = result["result"]
                elif result.get("message"):
                    summary = result["message"]
            elif hasattr(result, "success") and hasattr(result, "unwrap"):
                if result.success:
                    summary = str(result.unwrap())
                else:
                    summary = str(result.error)
            elif isinstance(result, str):
                summary = result
            elif result:
                summary = str(result)

            status = "✅ SUCCESS" if success else "❌ FAILED"
            parts.append(f"- {tool_name}: {status} - {summary}")

            # Add resolution hints for failures
            if not success and "already exists" in summary.lower():
                parts.append("  💡 HINT: File conflict - consider unique filename or overwrite")
            elif not success and "permission" in summary.lower():
                parts.append("  💡 HINT: Permission issue - try alternative path or clarification")
            elif not success and "not found" in summary.lower():
                parts.append("  💡 HINT: Resource not found - verify path or create dependencies")
        
        return "\n".join(parts)


def create_execution(max_iterations: int = 10) -> Execution:
    """Create fresh execution state for task."""
    return Execution(max_iterations=max_iterations)


def set_tool_calls(execution: Execution, calls: list[dict[str, Any]]) -> None:
    """Set pending tool calls in execution state."""
    execution.pending_calls = calls


def finish_tools(execution: Execution, results: list[dict[str, Any]]) -> None:
    """Move pending calls to completed and store results."""
    execution.completed_calls.extend(results)
    execution.pending_calls = []


__all__ = ["Execution", "ExecutionContext", "create_execution", "set_tool_calls", "finish_tools"]