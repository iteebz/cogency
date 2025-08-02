"""Reasoning pipeline - orchestrates focused reasoning components."""

from typing import List, Optional

from cogency.providers import LLM
from cogency.state import AgentState, build_reasoning_prompt
from cogency.tools import Tool

from .context import Context
from .mode import Mode
from .parser import Parse
from .prompt import Prompt


class Reason:
    """Orchestrates reasoning components in clean pipeline."""

    def __init__(self, llm: LLM, tools: List[Tool], memory=None):
        self.llm = llm
        self.tools = tools
        self.memory = memory

        # Initialize components
        self.context = Context()
        self.prompt = Prompt()
        self.parse = Parse()
        self.mode = Mode()

    async def process(self, state: AgentState, notifier) -> Optional[str]:
        """Execute reasoning pipeline with canonical architecture."""
        # Get current state
        iteration = state.execution.iteration
        mode = state.execution.mode

        await notifier("reason", state=mode)

        # Check stop conditions
        if iteration >= state.execution.max_iterations:
            state.execution.stop_reason = "depth_reached"
            await notifier(
                "trace", message="ReAct terminated", reason="depth_reached", iterations=iteration
            )
            return None

        # Build reasoning prompt using pure function
        reasoning_prompt = build_reasoning_prompt(state, self.tools, mode)

        # Trace reasoning context for debugging
        if iteration == 0:
            await notifier(
                "trace",
                message="ReAct loop initiated",
                mode=mode,
                depth_limit=state.execution.max_iterations,
            )

        # Execute LLM reasoning
        messages = [{"role": "system", "content": reasoning_prompt}]
        messages.extend(
            [{"role": msg["role"], "content": msg["content"]} for msg in state.execution.messages]
        )

        import asyncio

        await asyncio.sleep(0)  # Yield for UI

        llm_result = await self.llm.run(messages)
        from resilient_result import unwrap

        raw_response = unwrap(llm_result)

        # Parse JSON response
        from cogency.utils import parse_json

        parsed = parse_json(raw_response)

        if not parsed.success:
            # Fallback to direct response
            if raw_response and not raw_response.strip().startswith("{"):
                state.execution.response = raw_response.strip()
                await notifier("reason", state="direct_response", content=raw_response[:100])
                return raw_response.strip()
            return None

        reasoning_data = parsed.data

        # Update state from reasoning response
        state.update_from_reasoning(reasoning_data)

        # Display reasoning
        thinking = reasoning_data.get("thinking", "")
        if thinking:
            await notifier("reason", state="thinking", content=thinking)

        # Check for direct response
        if state.execution.response:
            await notifier(
                "reason", state="direct_response", content=state.execution.response[:100]
            )
            return state.execution.response

        return None

    async def _display_reasoning(self, reasoning_response, notifier, mode):
        """Display reasoning phases based on mode."""
        if not reasoning_response:
            return

        if mode == "deep":
            if reasoning_response.thinking:
                await notifier("reason", state="thinking", content=reasoning_response.thinking)
            if getattr(reasoning_response, "reflect", None):
                await notifier("reason", state="reflect", content=reasoning_response.reflect)
            if getattr(reasoning_response, "plan", None):
                await notifier("reason", state="plan", content=reasoning_response.plan)
        elif reasoning_response.thinking:
            await notifier("reason", state="thinking", content=reasoning_response.thinking)
