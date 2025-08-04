"""Agent execution engine - handles all complexity."""

from typing import Any, Optional

from resilient_result import Result

from cogency.config import MemoryConfig, ObserveConfig, PersistConfig, RobustConfig
from cogency.config.dataclasses import AgentConfig, _setup_config
from cogency.events import ConsoleHandler, LoggerHandler, MessageBus, init_bus
from cogency.memory import ImpressionSynthesizer
from cogency.observe import get_metrics_handler
from cogency.persist.store.base import _setup_persist
from cogency.persist.utils import _get_state
from cogency.providers.setup import _setup_embed, _setup_llm
from cogency.security import assess
from cogency.state import AgentMode, AgentState
from cogency.steps.composition import _setup_steps
from cogency.steps.execution import execute_agent
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
        self._initialized = True

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
        self.config = config
        self.persistence = persistence

        self.steps = _setup_steps(
            self.llm, self.tools, self.memory, self.identity, self.output_schema, self.config
        )

    async def cleanup(self):
        """Clean up agent resources and emit teardown events."""
        if not self._initialized:
            return

        from cogency.events import emit

        try:
            emit("agent_teardown", name=self.name, status="cleaning")

            # Clean up resources
            if self.memory:
                emit("teardown", component="memory", status="cleaning")
                # Memory cleanup would go here
                emit("teardown", component="memory", status="complete")

            if self.persistence:
                emit("teardown", component="persistence", status="cleaning")
                # Persistence cleanup would go here
                emit("teardown", component="persistence", status="complete")

            # Clear state
            self.user_states.clear()
            self.last_state = None
            self._initialized = False

            emit("agent_teardown", name=self.name, status="complete")

        except Exception as e:
            emit("agent_teardown", name=self.name, status="error", error=str(e))
            raise

    def __del__(self):
        """Ensure cleanup on garbage collection."""
        if self._initialized:
            # Sync cleanup - best effort
            import asyncio

            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.create_task(self.cleanup())
                else:
                    asyncio.run(self.cleanup())
            except Exception:
                pass  # Ignore errors during cleanup

    @classmethod
    async def create(cls, name: str) -> "AgentExecutor":
        """Create executor with default configuration."""
        from cogency.events import component, init_bus

        # Setup bus
        bus = MessageBus()
        logger_handler = LoggerHandler()
        bus.subscribe(logger_handler)
        init_bus(bus)

        # Beautiful component setup with invisible events
        @component("llm")
        def setup_llm():
            return _setup_llm(None)

        @component("embed")
        def setup_embed():
            # Only setup embed if memory will be used
            return None

        @component("tools")
        def setup_tools():
            return _setup_tools([], None)

        @component("config")
        def setup_config():
            config = AgentConfig()
            config.robust = _setup_config(RobustConfig, False)
            config.observe = ObserveConfig()  # Sensible defaults
            config.persist = _setup_config(PersistConfig, False)
            config.memory = _setup_config(MemoryConfig, False)
            return config

        # Execute setup - events emitted automatically
        llm = setup_llm()
        embed = setup_embed()
        tools = setup_tools()
        config = setup_config()

        return cls(
            name=name,
            llm=llm,
            embed=embed,
            tools=tools,
            memory=None,
            config=config,
            persistence=None,
        )

    @classmethod
    async def configure(cls, config) -> "AgentExecutor":
        """Create executor from builder config."""
        from cogency.events import (
            LoggerHandler,
            MessageBus,
            component,
        )

        # Setup unified events system
        bus = MessageBus()
        bus.subscribe(ConsoleHandler(config.notify, config.debug))
        bus.subscribe(LoggerHandler())  # For agent.logs()
        bus.subscribe(get_metrics_handler())

        # Add custom handlers
        if config.handlers:
            for handler in config.handlers:
                bus.subscribe(handler)

        init_bus(bus)

        # Beautiful component setup
        @component("persist")
        def setup_persist():
            return _setup_config(
                PersistConfig,
                config.persist,
                store=getattr(config.persist, "store", None)
                if hasattr(config.persist, "store")
                else None,
            )

        @component("memory")
        def setup_memory():
            return _setup_config(MemoryConfig, config.memory)

        @component("robust")
        def setup_robust():
            return _setup_config(RobustConfig, config.robust)

        @component("llm")
        def setup_llm():
            return _setup_llm(config.llm)

        @component("embed")
        def setup_embed():
            # Only setup embed if memory is enabled
            memory_cfg = _setup_config(MemoryConfig, config.memory)
            if memory_cfg:
                return _setup_embed(config.embed)
            return None

        @component("tools")
        def setup_tools():
            return _setup_tools(config.tools or [], None)

        # Execute setup - events emitted invisibly
        persist_config = setup_persist()
        memory_config = setup_memory()
        robust_config = setup_robust()

        agent_config = AgentConfig()
        agent_config.robust = robust_config
        # Handle observe config - True/False/ObserveConfig
        if config.observe is True:
            agent_config.observe = ObserveConfig()  # Sensible defaults
        elif config.observe is False:
            agent_config.observe = None
        elif isinstance(config.observe, ObserveConfig):
            agent_config.observe = config.observe
        else:
            agent_config.observe = ObserveConfig()  # Default to basic
        agent_config.persist = persist_config
        agent_config.memory = memory_config

        llm = setup_llm()
        embed = setup_embed()
        tools = setup_tools()

        if memory_config:
            store = memory_config.store or (persist_config.store if persist_config else None)
            memory = ImpressionSynthesizer(llm, store=store)
            memory.synthesis_threshold = memory_config.synthesis_threshold
        else:
            memory = None

        persistence = _setup_persist(persist_config)

        return cls(
            name=config.name,
            llm=llm,
            embed=embed,
            tools=tools,
            memory=memory,
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

    async def _execution_state(self, query: str, user_id: str = "default") -> AgentState:
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

        # SEC-002: Command injection protection via input validation
        security_result = await assess(query)
        if not security_result.safe:
            raise ValueError("Security violation: Dangerous patterns detected")

        wrapped_query = f"[user]\n{query.strip()}\n[/user]"
        state.execution.add_message("user", wrapped_query)

        # Memory operations
        if self.memory:
            await self.memory.load(user_id)
            await self.memory.remember(query, human=True)
            # CRITICAL FIX: Connect memory to AgentState for context injection
            user_profile = await self.memory._load_profile(user_id)
            state.user_profile = user_profile

        # Set agent mode
        state.execution.mode = self.mode

        return state

    async def run(self, query: str, user_id: str = "default", identity: str = None) -> str:
        """Execute agent and return complete response."""
        try:
            # Setup execution state
            state = await self._execution_state(query, user_id)

            # Setup steps with runtime identity (if provided)
            if identity:
                steps = _setup_steps(
                    self.llm, self.tools, self.memory, identity, self.output_schema, self.config
                )
            else:
                steps = self.steps

            # Execute steps - events system already set up in configure()
            from cogency.events import emit

            # Start notification
            emit("start", query=query)

            await execute_agent(
                state,
                steps["triage"],
                steps["reason"],
                steps["act"],
                steps["respond"],
                steps["synthesize"],
            )
            self.last_state = state

            # Extract response
            response = state.execution.response

            # Unwrap Result objects at the boundary
            if isinstance(response, Result):
                response = response.data if response.success else None

            # Learn from response
            if self.memory and response:
                await self.memory.remember(response, human=False)

            return response or "No response generated"

        except ValueError as e:
            # Handle validation errors from _execution_state
            return str(e)
        except Exception as e:
            import traceback

            from cogency.events import emit

            error_msg = f"Flow execution failed: {e}\n{traceback.format_exc()}"
            emit("error", message=error_msg)
            raise e

    def logs(self) -> list[dict[str, Any]]:
        """Execution logs summary. Always available for retrospective debugging."""
        from cogency.events import get_logs

        return get_logs(summary=True)
