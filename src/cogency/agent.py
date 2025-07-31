"""Cognitive agent with zero ceremony."""

from typing import Any, AsyncIterator

from cogency.executor import AgentExecutor
from cogency.state import State


class Agent:
    """Cognitive agent with zero ceremony."""

    def __init__(self, name: str = "cogency"):
        self.name = name
        self._executor = None
        self._config = None

    async def _get_executor(self) -> AgentExecutor:
        """Get or create executor."""
        if not self._executor:
            if self._config:
                self._executor = await AgentExecutor.from_config(self._config)
            else:
                self._executor = await AgentExecutor.create(self.name)
        return self._executor

    @property
    async def memory(self):
        """Access memory component (for tests/advanced usage)."""
        executor = await self._get_executor()
        return getattr(executor, "memory", None)

    async def run(self, query: str, user_id: str = "default") -> str:
        executor = await self._get_executor()
        return await executor.run(query, user_id)

    async def stream(self, query: str, user_id: str = "default") -> AsyncIterator[str]:
        executor = await self._get_executor()
        async for chunk in executor.stream(query, user_id):
            yield chunk

    def traces(self) -> list[dict[str, Any]]:
        if not self._executor:
            return []
        return self._executor.traces()

    @classmethod
    def _from_config(cls, config) -> "Agent":
        """Internal factory method for builder pattern."""
        agent = cls(config.name)
        # Defer executor creation until first use, but store config
        agent._config = config
        return agent


__all__ = ["Agent", "State"]
