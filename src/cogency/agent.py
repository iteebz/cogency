"""Cognitive agent with zero ceremony."""

from typing import Any, List, Union

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
        handlers: Custom event handlers for streaming, websockets, etc

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
        With events: Agent("assistant", handlers=[WebSocketHandler(ws)])
        Advanced: Agent("assistant", memory=MemoryConfig(threshold=8000))
    """

    def __init__(
        self,
        name: str = "cogency",
        *,
        tools: Union[List[str], List[Tool], str] = None,
        memory: Union[bool, MemoryConfig] = False,
        handlers: List[Any] = None,
        **config,
    ):
        from cogency.config.dataclasses import AgentConfig

        self.name = name
        self._executor = None
        self._handlers = handlers or []

        if tools is None:
            tools = []

        # Initialize advanced config
        advanced = _init_advanced_config(**config)

        self._config = AgentConfig()
        self._config.name = name
        self._config.tools = tools
        self._config.memory = memory
        self._config.handlers = self._handlers

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

    def logs(
        self,
        *,
        type: str = None,
        step: str = None,
        raw: bool = False,
        errors_only: bool = False,
        last: int = None,
    ) -> list[dict[str, Any]]:
        """Get execution logs with optional filtering.

        Args:
            type: Filter by event type ('tool', 'llm', 'tokens', 'error', etc.)
            step: Filter by execution step ('triage', 'reason', 'action', 'respond')
            raw: Return all raw events instead of summary (default False)
            errors_only: Return only error events
            last: Return only the last N events

        Returns:
            List of log events. Empty list if no logs match filters.
            By default returns high-level execution summary.

        Examples:
            Basic usage:
            >>> agent.logs()  # High-level execution path (default)
            >>> agent.logs(raw=True)  # All detailed events
            >>> agent.logs(errors_only=True)  # Just errors

            Filtering:
            >>> agent.logs(type='tool')  # Tool executions only
            >>> agent.logs(step='reason')  # Reasoning steps only
            >>> agent.logs(type='error', last=5)  # Recent 5 errors
        """
        from cogency.events import get_logs

        # Default to summary mode unless raw=True or specific filters are used
        summary = not raw and not type and not step and not errors_only
        
        return get_logs(type=type, step=step, summary=summary, errors_only=errors_only, last=last)


__all__ = ["Agent"]
