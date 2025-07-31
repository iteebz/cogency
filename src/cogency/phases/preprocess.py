"""Preprocess node - routing, memory extraction, tool filtering."""

from typing import List, Optional

from cogency.decorators import phase
from cogency.phases import Phase
from cogency.phases.preprocessing import PreprocessPipeline
from cogency.services import LLM
from cogency.state import State
from cogency.tools import Tool


class Preprocess(Phase):
    def __init__(self, llm, tools, memory, identity=None):
        super().__init__(
            preprocess,
            llm=llm,
            tools=tools,
            memory=memory,
            identity=identity,
        )


@phase.preprocess()
async def preprocess(
    state: State,
    notifier,
    llm: LLM,
    tools: List[Tool],
    memory,  # Impression instance or None
    identity: Optional[str] = None,
) -> Optional[str]:
    """Preprocess: routing decisions, memory extraction, tool selection."""
    pipeline = PreprocessPipeline(llm, tools, memory, identity)
    return await pipeline.process(state, notifier)
