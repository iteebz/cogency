"""Cognitive agent with zero ceremony."""

from typing import Any, AsyncIterator, List, Union

from cogency.config import MemoryConfig
from cogency.config.validation import init_advanced_config, validate_union_patterns
from cogency.runtime import AgentExecutor
from cogency.state import AgentState
from cogency.tools import Tool


class Agent:
    """Cognitive agent with zero ceremony.

    Args:
        name (str): Agent identifier (default "cogency")
        tools (list[str] | list[Tool] | str, optional): Tools to enable.
            Defaults to [] (no tools).
        memory (bool | MemoryConfig, optional): Enable memory.
            Set to `True` for default settings or provide a `MemoryConfig`
            object for advanced configuration. Defaults to `False`.

    Advanced configuration (via **config):
        identity (str, optional): Agent identity/persona
        mode (str): Reasoning mode - "adapt", "fast", or "deep" (default "adapt")
        depth (int): Max reasoning iterations (default 10)
        debug (bool): Enable debug mode (default False)
        notify (bool): Enable progress notifications (default True)
        robust (bool | RobustConfig, optional): Enable robustness features.
            Set to `True` for defaults or provide `RobustConfig` for custom
            retry/timeout/rate limiting settings. Defaults to `False`.
        observe (bool | ObserveConfig, optional): Enable observability.
            Set to `True` for default metrics or provide `ObserveConfig` for
            custom monitoring configuration. Defaults to `False`.
        persist (bool | PersistConfig, optional): Enable state persistence.
            Set to `True` for defaults or provide `PersistConfig` for custom
            storage backends. Defaults to `False`.

    Examples:
        Basic usage:
            agent = Agent("assistant")

        With memory and robustness:
            agent = Agent("assistant", memory=True, robust=True)

        Advanced configuration:
            agent = Agent(
                "assistant",
                memory=MemoryConfig(threshold=8000, user_id="alice"),
                robust=RobustConfig(attempts=5, timeout=120.0)
            )
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

        # Handle mutable default
        if tools is None:
            tools = []

        # Initialize advanced config
        advanced = init_advanced_config(**config)

        # Build config from parameters
        self._config = AgentConfig()
        self._config.name = name
        self._config.tools = tools
        self._config.memory = memory

        # Apply advanced config
        for key, value in advanced.items():
            setattr(self._config, key, value)

        # Validate Union pattern usage (council ruling compliance)
        validate_union_patterns(self._config)

    async def _get_executor(self) -> AgentExecutor:
        """Get or create executor."""
        if not self._executor:
            self._executor = await AgentExecutor.configure(self._config)
        return self._executor

    async def memory(self):
        """Access memory component."""
        executor = await self._get_executor()
        return getattr(executor, "memory", None)

    async def run(self, query: str, user_id: str = "default", identity: str = None) -> str:
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


__all__ = ["Agent", "AgentState"]
