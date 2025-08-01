"""Preparing pipeline - orchestrates focused components."""

from typing import List, Optional

from cogency.providers import LLM
from cogency.state import State
from cogency.tools import Tool

from .context import Context
from .extract import Extract
from .route import Route
from .select import Select


class Flow:
    """Orchestrates prepare components in clean pipeline."""

    def __init__(self, llm: LLM, tools: List[Tool], memory=None):
        self.llm = llm
        self.tools = tools
        self.memory = memory

        # Initialize components
        self.context = Context(llm)
        self.extract = Extract(llm)
        self.select = Select(llm)
        self.route = Route(llm)

    async def process(self, state: State, notifier) -> Optional[str]:
        """Execute preparing pipeline with early returns."""
        query = state.query

        # Skip if no tools available - handle direct response
        if not self.tools:
            return await self.route.check_early_return(query, [])

        # Step 1: Extract memory (async, non-blocking)
        memory_result = await self.extract.extract(query)
        if self.memory:
            await self.extract.save_memory(memory_result, self.memory, notifier)

        # Step 2: Select tools
        selection_result = await self.select.select(query, self.tools)
        filtered_tools = self.select.filter_tools(self.tools, selection_result.selected_tools)

        # Step 3: Check for early return
        early_response = await self.route.check_early_return(query, filtered_tools)
        if early_response:
            return early_response

        # Step 4: Build context
        classification = await self.context.build(query)

        # Step 5: Update state for ReAct phase
        state.selected_tools = filtered_tools
        state.mode = classification.mode
        state.iteration = 0

        # Step 6: Notify about tool selection
        await self._notify_tool_selection(notifier, filtered_tools)

        return None  # Continue to reason phase

    async def _notify_tool_selection(self, notifier, filtered_tools: List[Tool]) -> None:
        """Send appropriate notifications about tool selection."""
        if not filtered_tools:
            return

        total_tools = len(self.tools)
        selected_count = len(filtered_tools)

        if selected_count < total_tools:
            await notifier(
                "prepare",
                state="filtered",
                selected_tools=selected_count,
                total_tools=total_tools,
            )
        elif selected_count == 1:
            await notifier("prepare", state="direct", tool_count=1)
        else:
            await notifier("prepare", state="react", tool_count=selected_count)
