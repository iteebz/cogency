"""Reason node - pure reasoning and decision making."""

from typing import List, Optional

from cogency.providers import LLM
from cogency.state import State
from cogency.tools import Tool

from .flow import Flow


async def reason(
    state: State,
    notifier,
    llm: LLM,
    tools: List[Tool],
    memory,  # Impression instance or None
) -> Optional[str]:
    """Reason: focused reasoning and decision making."""
    pipeline = Flow(llm, tools, memory)
    return await pipeline.process(state, notifier)
