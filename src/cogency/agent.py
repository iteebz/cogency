"""Cognitive agent with zero ceremony."""

from typing import Any, AsyncIterator, Dict, List, Union

from cogency.config import MemoryConfig
from cogency.runtime import AgentExecutor
from cogency.state import State
from cogency.tools import Tool


class Agent:
    """Cognitive agent with zero ceremony.

    Core affordances:
        name: Agent identifier
        tools: List of tools/tool names, or 'all' for full access (default [])
        memory: Enable/configure memory (bool or MemoryConfig)

    Advanced config options:
        identity: Agent identity/persona
        output_schema: JSON schema for structured output
        llm: Language model provider
        embed: Embedding provider
        mode: Execution mode ("adapt", "fast", "thorough")
        depth: Max reasoning depth (default 10)
        notify: Enable notifications (default True)
        debug: Debug mode (default False)
        formatter: Custom notification formatter
        on_notify: Custom notification callback
        robust: Robustness config (bool or RobustConfig, default False)
        observe: Observability config (bool or ObserveConfig, default False)
        persist: Persistence config (bool or PersistConfig, default False)
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
        advanced = self._init_advanced(**config)

        # Build config from parameters
        self._config = AgentConfig()
        self._config.name = name
        self._config.tools = tools
        self._config.memory = memory

        # Apply advanced config
        for key, value in advanced.items():
            setattr(self._config, key, value)

    def _init_advanced(self, **config) -> Dict[str, Any]:
        """Initialize and validate advanced configuration options."""

        # Known configuration keys with defaults
        known_keys = {
            "identity": None,
            "output_schema": None,
            "llm": None,
            "embed": None,
            "mode": "adapt",
            "depth": 10,
            "notify": True,
            "debug": False,
            "formatter": None,
            "on_notify": None,
            "robust": False,
            "observe": False,
            "persist": False,
        }

        # Validate all provided keys are known
        unknown_keys = set(config.keys()) - set(known_keys.keys())
        if unknown_keys:
            raise ValueError(f"Unknown config keys: {', '.join(sorted(unknown_keys))}")

        # Return config with defaults applied
        result = known_keys.copy()
        result.update(config)
        return result

    async def _get_executor(self) -> AgentExecutor:
        """Get or create executor."""
        if not self._executor:
            self._executor = await AgentExecutor.configure(self._config)
        return self._executor

    async def memory(self):
        """Access memory component."""
        executor = await self._get_executor()
        return getattr(executor, "memory", None)

    async def _debug_memory(self):
        """Access memory component (debug mode only)."""
        if not self._config.debug:
            raise RuntimeError("Memory access requires debug=True")
        executor = await self._get_executor()
        return getattr(executor, "memory", None)

    async def run(self, query: str, user_id: str = "default", identity: str = None) -> str:
        executor = await self._get_executor()
        return await executor.run(query, user_id, identity)

    async def _debug_tools(self):
        """Access tools (debug mode only)."""
        if not self._config.debug:
            raise RuntimeError("Tools access requires debug=True")
        executor = await self._get_executor()
        return getattr(executor, "tools", None)

    async def stream(self, query: str, user_id: str = "default") -> AsyncIterator[str]:
        executor = await self._get_executor()
        async for chunk in executor.stream(query, user_id):
            yield chunk

    def traces(self) -> list[dict[str, Any]]:
        if not self._executor:
            return []
        return self._executor.traces()


__all__ = ["Agent", "State"]
