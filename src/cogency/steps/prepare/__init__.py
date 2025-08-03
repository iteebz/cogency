"""Prepare step - routing, memory extraction, tool filtering.

The prepare step handles initial request processing:
- Routing decisions for request type
- Memory extraction and context building
- Tool selection and filtering

Internal implementation uses Flow pipeline for robust processing.
"""

from typing import List, Optional

from cogency.providers import LLM
from cogency.state import AgentState
from cogency.tools import Tool

from .flow import Flow


async def prepare(
    state: AgentState,
    notifier,
    llm: LLM,
    tools: List[Tool],
    memory,  # Impression instance or None
) -> Optional[str]:
    """Prepare: routing decisions, memory extraction, tool selection."""
    pipeline = Flow(llm, tools, memory)
    return await pipeline.process(state, notifier)
