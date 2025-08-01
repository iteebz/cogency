"""Prepare node - routing, memory extraction, tool filtering."""

from typing import List, Optional

from cogency.providers import LLM
from cogency.state import State
from cogency.tools import Tool

from .flow import Flow


async def prepare(
    state: State,
    notifier,
    llm: LLM,
    tools: List[Tool],
    memory,  # Impression instance or None
) -> Optional[str]:
    """Prepare: routing decisions, memory extraction, tool selection."""
    pipeline = Flow(llm, tools, memory)
    return await pipeline.process(state, notifier)
