"""Preprocessing pipeline - orchestrates focused components."""

from typing import List, Optional

from cogency.services import LLM
from cogency.state import State
from cogency.tools import Tool

from .classifier import QueryClassifier
from .extractor import MemoryExtractor
from .router import EarlyRouter
from .selector import ToolSelector


class PreprocessPipeline:
    """Orchestrates preprocessing components in clean pipeline."""

    def __init__(self, llm: LLM, tools: List[Tool], memory=None, identity: Optional[str] = None):
        self.llm = llm
        self.tools = tools
        self.memory = memory
        self.identity = identity

        # Initialize components
        self.classifier = QueryClassifier(llm)
        self.extractor = MemoryExtractor(llm)
        self.selector = ToolSelector(llm)
        self.router = EarlyRouter(llm)

    async def process(self, state: State, notifier) -> Optional[str]:
        """Execute preprocessing pipeline with early returns."""
        query = state.query

        # Skip if no tools available - handle direct response
        if not self.tools:
            return await self.router.check_early_return(query, [], self.identity)

        # Step 1: Extract memory (async, non-blocking)
        memory_result = await self.extractor.extract(query)
        if self.memory:
            await self.extractor.save_memory(memory_result, self.memory, notifier)

        # Step 2: Select tools
        selection_result = await self.selector.select(query, self.tools)
        filtered_tools = self.selector.filter_tools(self.tools, selection_result.selected_tools)

        # Step 3: Check for early return
        early_response = await self.router.check_early_return(query, filtered_tools, self.identity)
        if early_response:
            return early_response

        # Step 4: Classify complexity
        classification = await self.classifier.classify(query)

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
                "preprocess",
                state="filtered",
                selected_tools=selected_count,
                total_tools=total_tools,
            )
        elif selected_count == 1:
            await notifier("preprocess", state="direct", tool_count=1)
        else:
            await notifier("preprocess", state="react", tool_count=selected_count)
