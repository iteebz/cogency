"""Recovery strategies - unified patterns."""

from typing import Any

from cogency.utils.results import RecoveryResult

from .exceptions import ActionError, ParsingError, PreprocessError, ReasoningError, ResponseError


class RecoveryStrategies:
    """Beautiful recovery strategies that read like English."""

    @staticmethod
    async def preprocess(error: PreprocessError, state: Any) -> RecoveryResult:
        """Preprocessing recovery - continue without memory if needed."""
        if error.memory_failed:
            state["memory_enabled"] = False
            return RecoveryResult.ok(state, recovery_action="disable_memory")
        return RecoveryResult.ok(state, recovery_action="skip_enrichment")

    @staticmethod
    async def reasoning(error: ReasoningError, state: Any) -> RecoveryResult:
        """Reasoning recovery - mode fallback and loop breaking."""
        if error.loop_detected:
            state["next_node"] = "respond"
            state["stopping_reason"] = "loop_recovery"
            return RecoveryResult.ok(state, recovery_action="force_respond")

        if error.mode == "deep":
            state["react_mode"] = "fast"
            return RecoveryResult.ok(state, recovery_action="fallback_to_fast")

        state["next_node"] = "respond"
        state["stopping_reason"] = "reasoning_error"
        return RecoveryResult.ok(state, recovery_action="direct_response")

    @staticmethod
    async def parsing(error: ParsingError, state: Any) -> RecoveryResult:
        """Parsing recovery - fallback to empty structure."""
        # Let parse_json_with_correction handle the recovery
        return RecoveryResult.ok(state, recovery_action="fallback_parsing")

    @staticmethod
    async def action(error: ActionError, state: Any) -> RecoveryResult:
        """Action recovery - retry reasoning or force respond."""
        if not error.recoverable:
            state["next_node"] = "respond"
            state["stopping_reason"] = "non_recoverable_action_error"
            return RecoveryResult.ok(state, recovery_action="force_respond")

        state["execution_results"] = {
            "type": "error",
            "failed_tools": error.failed_tools,
            "error_msg": error.message,
        }
        state["next_node"] = "reason"
        return RecoveryResult.ok(state, recovery_action="retry_reasoning")

    @staticmethod
    async def response(error: ResponseError, state: Any) -> RecoveryResult:
        """Response recovery - use partial or fallback."""
        if error.has_partial_response:
            return RecoveryResult.ok(state, recovery_action="use_partial")

        state["direct_response"] = f"I encountered an issue generating a response: {error.message}"
        return RecoveryResult.ok(state, recovery_action="fallback_response")


# Create beautiful singleton
recover = RecoveryStrategies()
