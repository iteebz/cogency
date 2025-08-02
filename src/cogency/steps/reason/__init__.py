"""Reason node - pure reasoning and decision making."""

from typing import List, Optional

from cogency.providers import LLM
from cogency.state import AgentState
from cogency.tools import Tool

from .reason import Reason


async def reason(
    state: AgentState,
    notifier,
    llm: LLM,
    tools: List[Tool],
    memory,  # Impression instance or None
) -> Optional[str]:
    """Reason: focused reasoning and decision making."""
    pipeline = Reason(llm, tools, memory)
    return await pipeline.process(state, notifier)
