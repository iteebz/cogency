"""AI agent - zero ceremony interface."""

from typing import Any, Union

from cogency.config.validation import validate_config_keys
from cogency.context.memory import Memory
from cogency.providers import detect_embed, detect_llm
from cogency.tools.base import Tool


class Agent:
    """AI agent - zero ceremony interface.

    Args:
        identity: Agent persona (default "AI Assistant")
        tools: Tool instances - list of Tool objects
        memory: Enable memory - True for defaults or Memory instance
        handlers: Event handlers for streaming, websockets, etc

    Examples:
        Basic: Agent("assistant")
        With tools: Agent("assistant", tools=[Files(), Shell()])
        With memory: Agent("assistant", memory=True)
        Full setup: Agent("assistant", tools=[Files()], memory=True)
    """

    def __init__(
        self,
        identity: str = "AI Assistant",
        *,
        tools: list[Tool] = None,
        memory: Union[bool, Memory] = False,
        handlers: list = None,
        max_iterations: int = 5,
        **config,
    ):
        self.identity = identity
        self._handlers = handlers or []
        self.max_iterations = max_iterations

        if tools is None:
            tools = []

        # Validate config keys (prevent typos)
        validate_config_keys(**config)

        # Setup components with canonical providers
        self.llm = detect_llm()
        self.embed = detect_embed()

        # Setup memory with canonical universal system
        if memory is True:
            self.memory = Memory()
        elif memory:
            self.memory = memory
        else:
            self.memory = None

        # Store tools for reasoning and execution
        self.tools = self._setup_tools(tools)

        # Initialize event system for observability
        self._init_events()

    def _setup_tools(self, tools):
        """Setup and validate tools with registry integration."""
        if not tools:
            return []

        # Setup tools with validation and dependency injection
        from cogency.tools.registry import setup_tools

        return setup_tools(tools, self.embed)

    def _init_events(self):
        """Initialize event system with EventBuffer for logs() method."""
        from cogency.events import EventBuffer, MessageBus, init_bus

        # Create bus with EventBuffer for capturing events
        bus = MessageBus()
        buffer = EventBuffer()
        bus.subscribe(buffer)

        # Add any custom handlers from config
        for handler in self._handlers:
            bus.subscribe(handler)

        # Initialize global bus
        init_bus(bus)

    def get_memory(self):
        """Access memory component."""
        return self.memory

    def run_sync(
        self,
        query: str,
        user_id: str = "default",
        identity: str = None,
        conversation_id: str = None,
    ) -> tuple[str, str]:
        """Execute agent query synchronously.

        Sync wrapper around run() - canonical pattern.
        Returns (response, conversation_id) for caller persistence.
        """
        import asyncio

        try:
            # Try to get running event loop
            asyncio.get_running_loop()
            # If we're in an event loop, raise error with helpful message
            raise RuntimeError("Use run() when already in an event loop")
        except RuntimeError:
            # No event loop running, safe to create new one
            return asyncio.run(self.run(query, user_id, identity, conversation_id))

    async def stream(self, query: str, user_id: str = "default", identity: str = None):
        """Execute agent query with async streaming.

        Direct streaming without ceremony.
        Memory and data are isolated per user_id.
        """
        # TODO: Implement direct streaming from LLM provider
        # For now, fall back to non-streaming
        result, _ = await self.run(query, user_id, identity)
        yield result

    async def run(
        self,
        query: str,
        user_id: str = "default",
        identity: str = None,
        conversation_id: str = None,
    ) -> tuple[str, str]:
        """Execute agent query - canonical domain coordination."""
        from cogency.runner import run_agent

        return await run_agent(
            query=query,
            user_id=user_id,
            llm=self.llm,
            tools=self.tools,
            memory=self.memory,
            max_iterations=self.max_iterations,
            identity=identity or self.identity,
            conversation_id=conversation_id,
        )

    def logs(
        self,
        *,
        type: str = None,
        errors_only: bool = False,
        last: int = None,
        include_debug: bool = False,
    ) -> list[dict[str, Any]]:
        """Get execution logs with optional filtering."""

        # Create bridge to use debug filtering
        from cogency.events.logs import create_logs_bridge

        bridge = create_logs_bridge(None)

        filters = {}
        if type:
            filters["type"] = type
        if errors_only:
            filters["errors_only"] = True

        return bridge.get_recent(
            count=last, filters=filters if filters else None, include_debug=include_debug
        )


__all__ = ["Agent"]
