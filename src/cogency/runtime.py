"""Agent execution engine - handles all complexity."""

import asyncio
from typing import Any, AsyncIterator, Optional

from cogency.config import MemoryConfig, ObserveConfig, PersistConfig, RobustConfig, setup_config
from cogency.config.dataclasses import AgentConfig
from cogency.memory import Memory
from cogency.notify import Notifier, setup_formatter
from cogency.persist import get_state
from cogency.providers import setup_embed, setup_llm
from cogency.state import State
from cogency.steps import setup_steps
from cogency.tools import setup_tools
from cogency.utils import validate_query


class _ServiceRegistry:
    """Clean dependency injection - no global state."""

    def __init__(self):
        self.llm = None
        self.embed = None
        self.tools = None
        self.memory = None
        self.notifier = None
        self.config = None
        self.persistence = None


class AgentExecutor:
    """Handles all agent complexity - service setup, dependency injection, execution."""

    def __init__(self, name: str, registry: Any):
        self.name = name
        self._registry = registry
        self.user_states: dict[str, State] = {}
        self.last_state: Optional[dict] = None

        # Extract config properties
        self.mode = "adapt"
        self.depth = 10
        self.notify = True
        self.debug = False
        self.identity = ""
        self.output_schema = None
        self.on_notify = None

        # Setup dependencies
        self.llm = registry.llm
        self.embed = registry.embed
        self.tools = registry.tools
        self.memory = registry.memory
        self.notifier = registry.notifier
        self.config = registry.config
        self.persistence = registry.persistence

        # Setup phases
        self.phases = setup_steps(
            self.llm, self.tools, self.memory, self.identity, self.output_schema, self.config
        )

    @classmethod
    async def create(cls, name: str) -> "AgentExecutor":
        """Create executor with default configuration."""
        registry = _ServiceRegistry()

        # Setup services (default: no notifications for basic create)
        formatter = setup_formatter(notify=False)
        registry.notifier = Notifier(formatter)
        registry.llm = setup_llm(None, notifier=registry.notifier)
        registry.embed = setup_embed(None)
        registry.tools = setup_tools([], None)

        # Setup config
        registry.config = AgentConfig()
        registry.config.robust = setup_config(RobustConfig, False)
        registry.config.observe = setup_config(ObserveConfig, False)
        registry.config.persist = setup_config(PersistConfig, False)
        registry.config.memory = setup_config(MemoryConfig, False)

        registry.memory = None
        registry.persistence = None

        return cls(name, registry)

    @classmethod
    async def configure(cls, config) -> "AgentExecutor":
        """Create executor from builder config."""
        from cogency.persist import setup_persistence

        # Create registry with dependencies
        registry = _ServiceRegistry()

        # Setup configs first so they're available for provider setup
        persist_config = setup_config(
            PersistConfig,
            config.persist,
            store=getattr(config.persist, "store", None)
            if hasattr(config.persist, "store")
            else None,
        )
        memory_config = setup_config(MemoryConfig, config.memory)
        robust_config = setup_config(RobustConfig, config.robust)

        registry.config = AgentConfig()
        registry.config.robust = robust_config
        registry.config.observe = setup_config(ObserveConfig, config.observe)
        registry.config.persist = persist_config
        registry.config.memory = memory_config

        # Unified notification system: auto-enable unless explicitly disabled
        if config.notify is False:
            # Silent mode
            formatter = setup_formatter(notify=False)
            registry.notifier = Notifier(formatter)
        elif config.on_notify:
            # Custom callback mode
            formatter = setup_formatter(notify=True, debug=config.debug)
            registry.notifier = Notifier(formatter, config.on_notify)
        else:
            # Default mode: beautiful notifications to stdout
            formatter = setup_formatter(notify=True, debug=config.debug)

            def default_callback(notification):
                output = formatter.format(notification)
                if output:
                    print(output)

            registry.notifier = Notifier(formatter, default_callback)
        registry.llm = setup_llm(config.llm, notifier=registry.notifier)
        registry.embed = setup_embed(config.embed)
        registry.tools = setup_tools(config.tools or [], None)

        # Setup memory
        if memory_config:
            store = memory_config.store or (persist_config.store if persist_config else None)
            registry.memory = Memory(registry.llm, store=store, user_id=memory_config.user_id)
            registry.memory.synthesis_threshold = memory_config.synthesis_threshold
        else:
            registry.memory = None

        registry.persistence = setup_persistence(persist_config)

        # Create executor
        executor = cls(config.name, registry)
        executor.mode = config.mode
        executor.depth = config.depth
        executor.notify = config.notify
        executor.debug = config.debug
        executor.identity = config.identity or ""
        executor.output_schema = config.output_schema
        executor.on_notify = config.on_notify

        # Re-setup phases with updated config
        executor.phases = setup_steps(
            registry.llm,
            registry.tools,
            registry.memory,
            executor.identity,
            executor.output_schema,
            registry.config,
        )

        return executor

    def _setup_notifier(self, callback=None):
        """Setup notification system."""
        final_callback = callback or self.on_notify
        formatter = setup_formatter(notify=bool(final_callback), debug=self.debug)
        return Notifier(formatter, final_callback)

    async def run(self, query: str, user_id: str = "default", identity: str = None) -> str:
        """Execute agent and return complete response."""
        try:
            # Input validation
            error = validate_query(query)
            if error:
                return error

            # Get or create state
            state = await get_state(
                user_id,
                query,
                self.depth,
                self.user_states,
                self.config.persist,
            )

            state.add_message("user", query)

            # Memory operations
            if self.memory:
                await self.memory.load()
                await self.memory.remember(query, human=True)

            # Set agent mode
            state.agent_mode = self.mode
            if self.mode != "adapt":
                state.mode = self.mode

            # Setup phases with runtime identity (if provided)
            if identity:
                phases = setup_steps(
                    self.llm, self.tools, self.memory, identity, self.output_schema, self.config
                )
            else:
                phases = self.phases

            # Execute phases
            from cogency.steps.execution import execute_agent

            notifier = self._setup_notifier()
            # Store notifier for traces() method
            self.notifier = notifier

            await execute_agent(
                state,
                phases["prepare"],
                phases["reason"],
                phases["act"],
                phases["respond"],
                notifier,
            )
            self.last_state = state

            # Extract response
            response = getattr(state, "response", None)

            # Unwrap Result objects at the boundary
            from resilient_result import Result
            if isinstance(response, Result):
                response = response.data if response.success else None

            # Learn from response
            if self.memory and response:
                await self.memory.remember(response, human=False)

            return response or "No response generated"

        except Exception as e:
            import traceback

            error_msg = f"Flow execution failed: {e}\n{traceback.format_exc()}"
            if self.notifier:
                await self.notifier("error", message=error_msg)
            raise e

    async def stream(self, query: str, user_id: str = "default") -> AsyncIterator[str]:
        """Stream agent execution."""
        # Input validation
        error = validate_query(query)
        if error:
            yield f"{error}\n"
            return

        # Get or create state
        state = await get_state(
            user_id,
            query,
            self.depth,
            self.user_states,
            self.config.persist,
        )

        state.add_message("user", query)

        # Memory operations
        if self.memory:
            await self.memory.load()
            await self.memory.remember(query, human=True)

        # Setup streaming
        queue: asyncio.Queue[str] = asyncio.Queue()

        async def stream_callback(event_type: str, **data) -> None:
            state = data.get("state", "")
            content = data.get("content", "")
            message = data.get("message", "")

            if content:
                output = f"[{event_type}:{state}] {content[:60]}..."
            elif message:
                output = f"[{event_type}] {message}"
            elif state:
                output = f"[{event_type}:{state}]"
            else:
                output = f"[{event_type}]"

            await queue.put(output)

        notifier = self._setup_notifier(callback=stream_callback)

        # Execute
        from cogency.steps.execution import execute_agent

        task = asyncio.create_task(
            execute_agent(
                state,
                self.phases["prepare"],
                self.phases["reason"],
                self.phases["act"],
                self.phases["respond"],
                notifier,
            )
        )

        # Stream results
        try:
            while not task.done():
                try:
                    message = await asyncio.wait_for(queue.get(), timeout=0.1)
                    yield message
                except asyncio.TimeoutError:
                    continue

            # Drain remaining
            while not queue.empty():
                yield queue.get_nowait()

        finally:
            result = await task
            self.last_state = result

            # Learn from response
            if self.memory and result and hasattr(result, "response"):
                await self.memory.remember(result.response, human=False)

    def traces(self) -> list[dict[str, Any]]:
        """Get execution traces (debug mode only)."""
        if not self.debug:
            return []

        return self.notifier.messages
