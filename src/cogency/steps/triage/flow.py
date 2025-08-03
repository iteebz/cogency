"""Triage pipeline - single LLM call for all triage."""

from typing import List, Optional

from cogency.providers import LLM
from cogency.state import AgentState
from cogency.tools import Tool

from . import Triage


class Flow:
    """Single LLM call for all triage tasks."""

    def __init__(self, llm: LLM, tools: List[Tool], memory=None):
        self.llm = llm
        self.tools = tools
        self.memory = memory

        # Single unified component
        self.triage = Triage(llm)

    async def process(self, state: AgentState, notifier) -> Optional[str]:
        """Single LLM call for all triage tasks."""
        query = state.execution.query

        # Single unified triage call
        result = await self.triage.triage(query, self.tools)

        # Handle direct response (early return)
        if result.direct_response:
            state.execution.response = result.direct_response
            return result.direct_response

        # Handle memory extraction
        if result.memory_content and self.memory:
            await self._save_memory(result, notifier)

        # Filter selected tools
        filtered_tools = self._filter_tools(result.selected_tools)

        # Update state for ReAct step
        state.execution.mode = result.mode
        state.execution.iteration = 0

        # Notify about triage results
        await self._notify_triage(notifier, result, filtered_tools)

        return None  # Continue to reason step

    async def _save_memory(self, result, notifier) -> None:
        """Save extracted memory if present."""
        # Truncate for notification display
        content = result.memory_content
        if len(content) > 60:
            break_point = content.rfind(" ", 40, 60)
            if break_point == -1:
                break_point = 60
            display_content = f"{content[:break_point]}..."
        else:
            display_content = content

        await notifier("triage", state="memory_saved", content_preview=display_content)
        await self.memory.remember(content, human=True)

    def _filter_tools(self, selected_names: List[str]) -> List[Tool]:
        """Filter tools based on selection."""
        if not selected_names:
            return []

        selected_set = set(selected_names)
        filtered = [tool for tool in self.tools if tool.name in selected_set]

        return [tool for tool in filtered if tool.name != "memorize"]

    async def _notify_triage(self, notifier, result, filtered_tools: List[Tool]) -> None:
        """Send notifications about triage results."""
        if result.memory_content:
            # Memory notification already sent in _save_memory
            pass

        await self._notify_tool_selection(notifier, filtered_tools)

    async def _notify_tool_selection(self, notifier, filtered_tools: List[Tool]) -> None:
        """Send appropriate notifications about tool selection."""
        if not filtered_tools:
            return

        total_tools = len(self.tools)
        selected_count = len(filtered_tools)

        if selected_count < total_tools:
            await notifier(
                "triage",
                state="filtered",
                selected_tools=selected_count,
                total_tools=total_tools,
            )
        elif selected_count == 1:
            await notifier("triage", state="direct", tool_count=1)
        else:
            await notifier("triage", state="react", tool_count=selected_count)
