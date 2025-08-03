"""Agent execution engine - handles all complexity."""

import asyncio
from typing import Any, AsyncIterator, Optional

from cogency.config import MemoryConfig, ObserveConfig, PersistConfig, RobustConfig
from cogency.config.dataclasses import AgentConfig, _setup_config
from cogency.memory import ImpressionSynthesizer
from cogency.notify import Notifier, _setup_formatter
from cogency.persist.utils import _get_state
from cogency.providers.setup import _setup_embed, _setup_llm
from cogency.state import AgentMode, AgentState
from cogency.steps.composition import _setup_steps
from cogency.tools.registry import _setup_tools
from cogency.utils.validation import validate_query


class AgentExecutor:
    """Handles all agent complexity - explicit dependency injection, execution."""

    def __init__(
        self,
        name: str,
        llm,
        embed,
        tools,
        memory,
        notifier,
        config,
        persistence,
        mode: AgentMode = AgentMode.ADAPT,
        max_iterations: int = 10,
        notify: bool = True,
        debug: bool = False,
        identity: str = "",
        output_schema=None,
        on_notify=None,
    ):
        self.name = name
        self.user_states: dict[str, AgentState] = {}
        self.last_state: Optional[dict] = None

        # Config properties
        self.mode = mode
        self.max_iterations = max_iterations
        self.notify = notify
        self.debug = debug
        self.identity = identity
        self.output_schema = output_schema
        self.on_notify = on_notify

        # Dependencies
        self.llm = llm
        self.embed = embed
        self.tools = tools
        self.memory = memory
        self.notifier = notifier
        self.config = config
        self.persistence = persistence

        self.steps = _setup_steps(
            self.llm, self.tools, self.memory, self.identity, self.output_schema, self.config
        )

    @property
    def depth(self) -> int:
        """Alias for max_iterations (backwards compatibility)."""
        return self.max_iterations

    @classmethod
    async def create(cls, name: str) -> "AgentExecutor":
        """Create executor with default configuration."""
        # Setup services (default: no notifications for basic create)
        formatter = _setup_formatter(notify=False)
        notifier = Notifier(formatter)
        llm = _setup_llm(None, notifier=notifier)
        embed = _setup_embed(None)
        tools = _setup_tools([], None)

        # Setup config
        config = AgentConfig()
        config.robust = _setup_config(RobustConfig, False)
        config.observe = _setup_config(ObserveConfig, False)
        config.persist = _setup_config(PersistConfig, False)
        config.memory = _setup_config(MemoryConfig, False)

        memory = None
        persistence = None

        return cls(
            name=name,
            llm=llm,
            embed=embed,
            tools=tools,
            memory=memory,
            notifier=notifier,
            config=config,
            persistence=persistence,
        )

    @classmethod
    async def configure(cls, config) -> "AgentExecutor":
        """Create executor from builder config."""
        from cogency.persist.store.base import _setup_persist

        # Setup configs first so they're available for provider setup
        persist_config = _setup_config(
            PersistConfig,
            config.persist,
            store=(
                getattr(config.persist, "store", None) if hasattr(config.persist, "store") else None
            ),
        )
        memory_config = _setup_config(MemoryConfig, config.memory)
        robust_config = _setup_config(RobustConfig, config.robust)

        agent_config = AgentConfig()
        agent_config.robust = robust_config
        agent_config.observe = _setup_config(ObserveConfig, config.observe)
        agent_config.persist = persist_config
        agent_config.memory = memory_config

        # Unified notification system: auto-enable unless explicitly disabled
        if config.notify is False:
            # Silent mode
            formatter = _setup_formatter(notify=False)
            notifier = Notifier(formatter)
        elif config.on_notify:
            # Custom callback mode
            formatter = _setup_formatter(notify=True, debug=config.debug)
            notifier = Notifier(formatter, config.on_notify)
        else:
            # Default mode: beautiful notifications to stdout
            formatter = _setup_formatter(notify=True, debug=config.debug)

            def default_callback(notification):
                output = formatter.format(notification)
                if output:
                    print(output)

            notifier = Notifier(formatter, default_callback)

        llm = _setup_llm(config.llm, notifier=notifier)
        embed = _setup_embed(config.embed)
        tools = _setup_tools(config.tools or [], None)

        if memory_config:
            store = memory_config.store or (persist_config.store if persist_config else None)
            memory = ImpressionSynthesizer(llm, store=store)
            memory.synthesis_threshold = memory_config.synthesis_threshold
        else:
            memory = None

        persistence = _setup_persist(persist_config)

        # Create executor with explicit dependencies
        return cls(
            name=config.name,
            llm=llm,
            embed=embed,
            tools=tools,
            memory=memory,
            notifier=notifier,
            config=agent_config,
            persistence=persistence,
            mode=config.mode,
            max_iterations=config.max_iterations,
            notify=config.notify,
            debug=config.debug,
            identity=config.identity or "",
            output_schema=config.output_schema,
            on_notify=config.on_notify,
        )

    def _setup_notifier(self, callback=None):
        """Setup notification system."""
        final_callback = callback or self.on_notify
        formatter = _setup_formatter(notify=bool(final_callback), debug=self.debug)
        return Notifier(formatter, final_callback)

    async def _setup_execution_state(self, query: str, user_id: str = "default") -> AgentState:
        """Common setup logic for both run() and stream() methods."""
        # Input validation
        error = validate_query(query)
        if error:
            raise ValueError(error)

        # Get or create state
        state = await _get_state(
            user_id,
            query,
            self.max_iterations,
            self.user_states,
            self.config.persist,
        )

        state.execution.add_message("user", query)

        # Memory operations
        if self.memory:
            await self.memory.load()
            await self.memory.remember(query, human=True)

        # Set agent mode
        state.execution.mode = self.mode

        return state

    async def run(self, query: str, user_id: str = "default", identity: str = None) -> str:
        """Execute agent and return complete response."""
        try:
            # Setup execution state
            state = await self._setup_execution_state(query, user_id)

            # Setup phases with runtime identity (if provided)
            if identity:
                steps = _setup_steps(
                    self.llm, self.tools, self.memory, identity, self.output_schema, self.config
                )
            else:
                steps = self.steps

            # Execute steps
            from cogency.steps.execution import execute_agent

            notifier = self._setup_notifier()
            # Store notifier for traces() method
            self.notifier = notifier

            await execute_agent(
                state,
                steps["prepare"],
                steps["reason"],
                steps["act"],
                steps["respond"],
                notifier,
            )
            self.last_state = state

            # Extract response
            response = state.execution.response

            # Unwrap Result objects at the boundary
            from resilient_result import Result

            if isinstance(response, Result):
                response = response.data if response.success else None

            # Learn from response
            if self.memory and response:
                await self.memory.remember(response, human=False)

            return response or "No response generated"

        except ValueError as e:
            # Handle validation errors from _setup_execution_state
            return str(e)
        except Exception as e:
            import traceback

            error_msg = f"Flow execution failed: {e}\n{traceback.format_exc()}"
            if self.notifier:
                await self.notifier("error", message=error_msg)
            raise e

    async def stream(self, query: str, user_id: str = "default") -> AsyncIterator[str]:
        """Stream agent execution."""
        try:
            # Setup execution state
            state = await self._setup_execution_state(query, user_id)
        except ValueError as e:
            yield f"{str(e)}\n"
            return

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
                self.steps["prepare"],
                self.steps["reason"],
                self.steps["act"],
                self.steps["respond"],
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
            if self.memory and result and hasattr(result.execution, "response"):
                await self.memory.remember(result.execution.response, human=False)

    def traces(self) -> list[dict[str, Any]]:
        """Get execution traces (debug mode only)."""
        if not self.debug:
            return []

        return self.notifier.messages
