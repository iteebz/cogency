"""Agent: Pure function interface to LLM reasoning."""

from contextlib import suppress

from .context import inject_context, persist_conversation_async
from .providers.openai import generate


class Agent:
    """Stateless context-driven agent.

    Examples:
        agent = Agent()
        response = await agent("What is 2+2?")
    """

    def __init__(self):
        pass

    async def __call__(self, query: str, user_id: str = "default") -> str:
        """Execute agent query - pure function interface."""
        context = inject_context(query, user_id)
        full_prompt = f"{context}\n\nQuery: {query}" if context else query
        response = await generate(full_prompt)

        # Optional persistence (fire and forget)
        with suppress(Exception):
            await persist_conversation_async(user_id, query, response)

        return response
