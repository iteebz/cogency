"""Beautiful recovery - Result-first phase recovery that reads like English."""

from typing import Dict, Union

from resilient_result import Result

from cogency.state import AgentState


class Recovery:
    """Beautiful recovery strategies - auto-discovery, zero ceremony."""

    @staticmethod
    async def recover(result: Result, state: AgentState, phase: str) -> Result:
        """Beautiful recovery - handles any phase failure gracefully.

        Args:
            result: The failed Result from a phase
            state: Current workflow state
            phase: Phase name (prepare, reasoning, action, response)

        Returns:
            Result with recovery actions applied to state
        """
        return result if result.success else await Recovery._route(result.error, state, phase)

    @staticmethod
    async def _route(error_data: Union[str, Dict], state: AgentState, phase: str) -> Result:
        """Auto-discover recovery method by phase name."""
        # Normalize error to dict for consistent handling
        if isinstance(error_data, str):
            error_data = {"message": error_data}

        # Auto-discover recovery method
        method_name = f"_{phase}"
        if hasattr(Recovery, method_name):
            method = getattr(Recovery, method_name)
            return await method(error_data, state)

        return await Recovery._fallback(error_data, state, phase)

    @staticmethod
    async def _prepare(error: Dict, state: AgentState) -> Result:
        """Preparing recovery - continue without memory if needed."""
        if error.get("memory_failed"):
            state.memory_enabled = False
            return Result.ok({"state": state, "recovery": "disable_memory"})

        return Result.ok({"state": state, "recovery": "skip_enrichment"})

    @staticmethod
    async def _reasoning(error: Dict, state: AgentState) -> Result:
        """Reasoning recovery - mode fallback and loop breaking."""
        if error.get("loop_detected"):
            state.next_step = "respond"
            state.execution.stop_reason = "loop_recovery"
            return Result.ok({"state": state, "recovery": "force_respond"})

        if error.get("mode") == "deep":
            state.execution.mode = "fast"
            return Result.ok({"state": state, "recovery": "fallback_to_fast"})

        # Default: skip to response
        state.next_step = "respond"
        state.execution.stop_reason = "reasoning_error"
        return Result.ok({"state": state, "recovery": "skip_to_response"})

    @staticmethod
    async def _parsing(error: Dict, state: AgentState) -> Result:
        """Parsing recovery - fallback to empty structure."""
        return Result.ok({"state": state, "recovery": "fallback_parsing"})

    @staticmethod
    async def _action(error: Dict, state: AgentState) -> Result:
        """Action recovery - retry reasoning or force respond."""
        if not error.get("recoverable", True):
            state.next_step = "respond"
            state.execution.stop_reason = "non_recoverable_action_error"
            return Result.ok({"state": state, "recovery": "force_respond"})

        # Store error context for retry
        state.execution_results = {
            "type": "error",
            "failed_tools": error.get("failed_tools", []),
            "error_msg": error.get("message", "Unknown action error"),
        }
        state.next_step = "reason"
        return Result.ok({"state": state, "recovery": "retry_reasoning"})

    @staticmethod
    async def _response(error: Dict, state: AgentState) -> Result:
        """Response recovery - use partial or fallback."""
        if error.get("has_partial_response"):
            return Result.ok({"state": state, "recovery": "use_partial"})

        # Fallback response
        message = error.get("message", "Unknown error")
        state.execution.response = f"I encountered an issue generating a response: {message}"
        return Result.ok({"state": state, "recovery": "fallback_response"})

    @staticmethod
    async def _fallback(error: Dict, state: AgentState, phase: str) -> Result:
        """Universal fallback - graceful degradation for unknown phases."""
        state.next_step = "respond"
        state.execution.stop_reason = f"{phase}_error_fallback"
        return Result.ok({"state": state, "recovery": f"fallback_{phase}"})


# Beautiful singleton - zero ceremony
recovery = Recovery()
