"""Recovery strategies - unified patterns."""

from typing import Any

from resilient_result import Result

from .exceptions import ActionError, ParsingError, PreprocessError, ReasoningError, ResponseError


class Recovery:
    """Beautiful recovery strategies that read like English."""

    @staticmethod
    async def preprocess(error: PreprocessError, state: Any) -> Result:
        """Preprocessing recovery - continue without memory if needed."""
        if error.memory_failed:
            state["memory_enabled"] = False
            return Result.ok(state, recovery_action="disable_memory")
        return Result.ok(state, recovery_action="skip_enrichment")

    @staticmethod
    async def reasoning(error: ReasoningError, state: Any) -> Result:
        """Reasoning recovery - mode fallback and loop breaking."""
        if error.loop_detected:
            state["next_phase"] = "respond"
            state["stop_reason"] = "loop_recovery"
            return Result.ok(state, recovery_action="force_respond")

        if error.mode == "deep":
            state["react_mode"] = "fast"
            return Result.ok(state, recovery_action="fallback_to_fast")

        state["next_phase"] = "respond"
        state["stop_reason"] = "reasoning_error"
        return Result.ok(state, recovery_action="response")

    @staticmethod
    async def parsing(error: ParsingError, state: Any) -> Result:
        """Parsing recovery - fallback to empty structure."""
        # Let parse_json_with_correction handle the recovery
        return Result.ok(state, recovery_action="fallback_parsing")

    @staticmethod
    async def action(error: ActionError, state: Any) -> Result:
        """Action recovery - retry reasoning or force respond."""
        if not error.recoverable:
            state["next_phase"] = "respond"
            state["stop_reason"] = "non_recoverable_action_error"
            return Result.ok(state, recovery_action="force_respond")

        state["execution_results"] = {
            "type": "error",
            "failed_tools": error.failed_tools,
            "error_msg": error.message,
        }
        state["next_phase"] = "reason"
        return Result.ok(state, recovery_action="retry_reasoning")

    @staticmethod
    async def response(error: ResponseError, state: Any) -> Result:
        """Response recovery - use partial or fallback."""
        if error.has_partial_response:
            return Result.ok(state, recovery_action="use_partial")

        state["response"] = f"I encountered an issue generating a response: {error.message}"
        return Result.ok(state, recovery_action="fallback_response")


# Create beautiful singleton
recovery = Recovery()
