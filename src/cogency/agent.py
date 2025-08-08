"""Cognitive agent with zero ceremony."""

from typing import Any, List, Union

from cogency.config import MemoryConfig
from cogency.config.validation import _init_advanced_config, validate_unions
from cogency.runtime import AgentRuntime
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
        notify: Enable progress notifications (default True)
        debug: Enable debug mode (default False)
        robust: Enable robustness - True for defaults or RobustConfig

    Examples:
        Basic: Agent("assistant")
        Production: Agent("assistant", notify=False)
        With events: Agent("assistant", handlers=[websocket_handler])
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

    async def _get_executor(self) -> AgentRuntime:
        """Get or create executor."""
        if not self._executor:
            self._executor = await AgentRuntime.configure(self._config)
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

    async def stream(self, query: str, user_id: str = "default", identity: str = None):
        """Stream agent response asynchronously.

        Args:
            query: User query to process
            user_id: User identifier for memory/state
            identity: Override agent identity for this query

        Yields:
            Agent response chunks
        """
        executor = await self._get_executor()
        async for chunk in executor.stream(query, user_id, identity):
            yield chunk

    def logs(
        self,
        *,
        mode: str = "summary",
        type: str = None,
        step: str = None,
        raw: bool = None,  # Deprecated, use mode="debug"
        errors_only: bool = False,
        last: int = None,
    ) -> list[dict[str, Any]]:
        """Get execution logs with optional filtering.

        Args:
            mode: Log mode - "summary" (default), "performance", "errors", "debug"
            type: Filter by event type (only for debug mode)
            step: Filter by execution step (only for debug mode)
            raw: Deprecated, use mode="debug" instead
            errors_only: Return only error events (deprecated, use mode="errors")
            last: Return only the last N events

        Returns:
            List of log events. Empty list if no logs match filters.
            By default returns developer-friendly execution summaries.

        Examples:
            Basic usage:
            >>> agent.logs()  # Execution summaries (default)
            >>> agent.logs(mode="performance")  # Performance analysis
            >>> agent.logs(mode="errors")  # Error analysis
            >>> agent.logs(mode="debug")  # Raw events

            Filtering:
            >>> agent.logs(mode="debug", type='tool')  # Tool events only
            >>> agent.logs(mode="debug", step='reason')  # Reasoning steps only
            >>> agent.logs(last=5)  # Recent 5 summaries
        """
        from cogency.events import get_logs

        # Handle deprecated parameters and determine summary mode
        if raw is True or errors_only:
            summary = False
        else:
            # Default behavior - use summary mode unless specific filters are applied
            if type is not None or step is not None:
                summary = False
            else:
                summary = True

        return get_logs(type=type, step=step, summary=summary, errors_only=errors_only, last=last)


__all__ = ["Agent"]
