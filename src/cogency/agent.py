"""Cognitive agent with zero ceremony."""

from typing import Any, AsyncIterator, List, Union

from cogency.config import MemoryConfig
from cogency.config.validation import _init_advanced_config, validate_unions
from cogency.runtime import AgentExecutor
from cogency.tools import Tool


class Agent:
    """Cognitive agent with zero ceremony.

    Args:
        name: Agent identifier (default "cogency")
        tools: Tools to enable - list of names, Tool objects, or single string
        memory: Enable memory - True for defaults or MemoryConfig for custom

    Advanced config (**kwargs):
        identity: Agent persona/identity
        mode: Reasoning mode - "adapt", "fast", or "deep" (default "adapt")
        max_iterations: Max reasoning iterations (default 10)
        debug: Enable debug mode (default False)
        notify: Enable progress notifications (default True)
        robust: Enable robustness - True for defaults or RobustConfig
        observe: Enable observability - True for defaults or ObserveConfig
        persist: Enable persistence - True for defaults or PersistConfig

    Examples:
        Basic: Agent("assistant")
        With features: Agent("assistant", memory=True, robust=True)
        Advanced: Agent("assistant", memory=MemoryConfig(threshold=8000))
    """

    def __init__(
        self,
        name: str = "cogency",
        *,
        tools: Union[List[str], List[Tool], str] = None,
        memory: Union[bool, MemoryConfig] = False,
        **config,
    ):
        from cogency.config.dataclasses import AgentConfig

        self.name = name
        self._executor = None

        if tools is None:
            tools = []

        # Initialize advanced config
        advanced = _init_advanced_config(**config)

        self._config = AgentConfig()
        self._config.name = name
        self._config.tools = tools
        self._config.memory = memory

        # Apply advanced config
        for key, value in advanced.items():
            setattr(self._config, key, value)

        validate_unions(self._config)

    async def _get_executor(self) -> AgentExecutor:
        """Get or create executor."""
        if not self._executor:
            self._executor = await AgentExecutor.configure(self._config)
        return self._executor

    async def memory(self):
        """Access memory component."""
        executor = await self._get_executor()
        return getattr(executor, "memory", None)

    def run(self, query: str, user_id: str = "default", identity: str = None) -> str:
        """Execute agent query synchronously.

        Args:
            query: User query to process
            user_id: User identifier for memory/state
            identity: Override agent identity for this query

        Returns:
            Agent response string
        """
        import asyncio

        return asyncio.run(self.run_async(query, user_id, identity))

    async def run_async(self, query: str, user_id: str = "default", identity: str = None) -> str:
        """Execute agent query asynchronously.

        Args:
            query: User query to process
            user_id: User identifier for memory/state
            identity: Override agent identity for this query

        Returns:
            Agent response string
        """
        executor = await self._get_executor()
        return await executor.run(query, user_id, identity)

    async def stream(self, query: str, user_id: str = "default") -> AsyncIterator[str]:
        executor = await self._get_executor()
        async for chunk in executor.stream(query, user_id):
            yield chunk

    def traces(self) -> list[dict[str, Any]]:
        if not self._executor:
            return []
        return self._executor.traces()


__all__ = ["Agent"]
