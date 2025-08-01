"""Reasoning pipeline - orchestrates focused reasoning components."""

from typing import List, Optional

from cogency.providers import LLM
from cogency.state import State
from cogency.tools import Tool

from .context import Context
from .mode import Mode
from .parser import Parse
from .prompt import Prompt


class Flow:
    """Orchestrates reasoning components in clean pipeline."""

    def __init__(self, llm: LLM, tools: List[Tool], memory=None, identity: Optional[str] = None):
        self.llm = llm
        self.tools = tools
        self.memory = memory
        self.identity = identity

        # Initialize components
        self.context = Context()
        self.prompt = Prompt()
        self.parse = Parse()
        self.mode = Mode()

    async def process(self, state: State, notifier) -> Optional[str]:
        """Execute reasoning pipeline with mode switching."""
        # Get current iteration and mode
        iteration = state.iteration
        mode = state.mode
        selected_tools = state.selected_tools or self.tools

        # Set react mode if different from current
        if state.mode != mode:
            state.mode = mode

        await notifier("reason", state=mode)

        # Check stop conditions
        if iteration >= state.depth:
            state.stop_reason = "depth_reached"
            state.tool_calls = None
            await notifier(
                "trace", message="ReAct terminated", reason="depth_reached", iterations=iteration
            )
            return None

        # Step 1: Build context
        context_data = await self.context.build(state, selected_tools, self.memory, mode, iteration)

        # Step 2: Build prompt
        reasoning_prompt = self.prompt.build(
            mode=mode,
            query=state.query,
            context_data=context_data,
            iteration=iteration,
            depth=state.depth,
            state=state,
            identity=self.identity,
        )

        # Trace reasoning context for debugging
        if iteration == 0:
            await notifier(
                "trace", message="ReAct loop initiated", mode=mode, depth_limit=state.depth
            )

        # Step 3: Execute LLM reasoning
        messages = state.conversation()
        messages.append({"role": "user", "content": state.query})
        messages.insert(0, {"role": "system", "content": reasoning_prompt})

        import asyncio

        await asyncio.sleep(0)  # Yield for UI
        llm_result = await self.llm.run(messages)

        from resilient_result import unwrap

        raw_response = unwrap(llm_result)

        # Step 4: Parse response
        reasoning_response = await self.parse.reasoning(raw_response, notifier, mode, iteration)

        # Step 5: Display reasoning phases
        await self._display_reasoning(reasoning_response, notifier, mode)

        # Step 6: Handle mode switching (preserve LLM-driven switching)
        await self.mode.handle_switch(state, raw_response, mode, iteration, notifier)

        # Step 7: Record action in state
        if reasoning_response:
            state.add_action(
                mode=state.mode,
                thinking=reasoning_response.thinking or "",
                planning=getattr(reasoning_response, "plan", "") or "",
                reflection=getattr(reasoning_response, "reflect", "") or "",
                approach=getattr(reasoning_response, "efficiency", "standard"),
                tool_calls=reasoning_response.tool_calls or [],
            )

            # Update workspace if provided
            if hasattr(reasoning_response, "updates") and reasoning_response.updates:
                state.update_workspace(reasoning_response.updates)

            # Set tool calls for action phase
            state.tool_calls = reasoning_response.tool_calls

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
