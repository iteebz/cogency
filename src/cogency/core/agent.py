"""Agent: Pure interface to ReAct algorithm."""

import time

from ..lib.providers import create_embedder, create_llm
from ..tools import BASIC_TOOLS
from .react import react, stream_react
from .types import AgentResult


class Agent:
    """Pure interface to ReAct algorithm."""

    def __init__(self, llm="openai", embedder=None, tools=None, max_iterations: int = 5):
        self.llm = create_llm(llm)
        self.embedder = create_embedder(embedder) if embedder else None
        self.tools = {t.name: t for t in (tools if tools is not None else BASIC_TOOLS)}
        self.max_iterations = max_iterations

    async def __call__(self, query: str, *, user_id: str = None) -> AgentResult:
        """Sacred interface with optional memory multitenancy."""
        final_event = await react(self.llm, self.tools, query, user_id, self.max_iterations)

        if final_event["type"] == "error":
            return AgentResult(
                f"LLM Error: {final_event['message']}", f"{user_id}_{int(time.time())}"
            )

        return AgentResult(final_event["answer"], final_event["conversation_id"])

    async def stream(self, query: str, *, user_id: str = None):
        """Stream ReAct reasoning states as structured events.

        Yields structured events for each ReAct loop iteration:
        - iteration: Loop iteration number
        - context: Context assembly completion
        - reasoning: LLM response content
        - tool: Tool execution results
        - complete: Final answer with conversation_id
        - error: Failure states

        Usage:
            async for event in agent.stream("Complex task"):
                if event["type"] == "reasoning":
                    print(f"Thinking: {event['content'][:100]}...")
        """
        async for event in stream_react(self.llm, self.tools, query, user_id, self.max_iterations):
            yield event
