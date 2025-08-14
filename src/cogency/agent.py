"""Agent: Pure function interface to LLM reasoning."""

from contextlib import suppress

from .context import context, persist
from .providers.openai import generate


class Agent:
    """Stateless context-driven agent."""

    def __init__(self):
        pass

    async def __call__(self, query: str, user_id: str = "default") -> str:
        """Execute query."""
        ctx = context(query, user_id)
        prompt = f"{ctx}\n\nQuery: {query}" if ctx else query
        response = await generate(prompt)

        with suppress(Exception):
            await persist(user_id, query, response)

        return response
