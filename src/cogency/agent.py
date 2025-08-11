"""Cognitive agent with zero ceremony."""

from typing import Any, List, Union

from cogency.config import MemoryConfig
from cogency.config.validation import validate_config_keys
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

        # Validate config keys (prevent typos)
        validate_config_keys(**config)

        # Create config with dataclass defaults
        self._config = AgentConfig(
            name=name,
            tools=tools,
            memory=memory,
            handlers=self._handlers,
            **config  # Apply user overrides
        )

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
        type: str = None,
        errors_only: bool = False,
        last: int = None,
    ) -> list[dict[str, Any]]:
        """Get execution logs with optional filtering.

        Args:
            type: Filter by event type
            errors_only: Return only error events
            last: Return only the last N events

        Returns:
            List of raw log events for debugging.

        Examples:
            Basic usage:
            >>> agent.logs()  # All events
            >>> agent.logs(type='tool')  # Tool events only
            >>> agent.logs(errors_only=True)  # Errors only
            >>> agent.logs(last=10)  # Recent 10 events
        """
        from cogency.events import get_logs

        return get_logs(type=type, errors_only=errors_only, last=last)


__all__ = ["Agent"]
