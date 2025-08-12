"""Cognitive agent with zero ceremony."""

from typing import Any, Union

from cogency.config.validation import validate_config_keys
from cogency.memory import Memory
from cogency.providers import detect_embed, detect_llm
from cogency.state import State


class Agent:
    """Cognitive agent with zero ceremony.

    Args:
        name: Agent identifier (default "cogency")
        tools: Tools to enable - list of names, Tool objects, or single string
        memory: Enable memory - True for defaults or Memory instance for custom
        handlers: Custom event handlers for streaming, websockets, etc

    Advanced config (**kwargs):
        identity: Agent persona/identity
        max_iterations: Max reasoning iterations (default 10)
        notify: Enable progress notifications (default True)

    Examples:
        Basic: Agent("assistant")
        With memory: Agent("assistant", memory=True)
        Production: Agent("assistant", notify=False)
        With events: Agent("assistant", handlers=[websocket_handler])
        Custom memory: Agent("assistant", memory=Memory())
    """

    def __init__(
        self,
        name: str = "cogency",
        *,
        tools: Union[list[str], list[Any], str] = None,
        memory: Union[bool, Any] = False,
        handlers: list[Any] = None,
        **config,
    ):
        from cogency.config.dataclasses import AgentConfig

        self.name = name
        self._handlers = handlers or []

        if tools is None:
            tools = []

        # Validate config keys (prevent typos)
        validate_config_keys(**config)

        # Create config with dataclass defaults
        agent_config = AgentConfig(
            name=name,
            tools=tools,
            memory=memory,
            handlers=self._handlers,
            **config,
        )

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

        self.max_iterations = getattr(agent_config, "max_iterations", 10)
        self.identity = getattr(agent_config, "identity", "")

        # Store tools for reasoning and execution
        self.tools = self._setup_tools(tools)

        # Initialize event system for observability
        self._init_events(agent_config)

    def _setup_tools(self, tools):
        """Setup and validate tools with registry integration."""
        if not tools:
            return []

        # Use _setup_tools from registry for validation and dependency injection
        from cogency.tools.registry import _setup_tools

        return _setup_tools(tools, self.embed)

    def _init_events(self, agent_config):
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

    def run(self, query: str, user_id: str = "default", identity: str = None) -> str:
        """Execute agent query synchronously."""
        import asyncio

        return asyncio.run(self.run_async(query, user_id, identity))

    async def run_async(self, query: str, user_id: str = "default", identity: str = None) -> str:
        """Execute agent query asynchronously."""
        from cogency.agents import act, reason
        from cogency.events import emit

        try:
            # Security check once per task
            from cogency.security.validation import validate_query

            security_error = validate_query(query)
            if security_error:
                emit("agent", state="security_violation", error=security_error)
                return security_error

            # Create execution state
            state = await State.start_task(query, user_id)

            # Memory operations - runtime user context
            if self.memory:
                await self.memory.load(user_id)
                await self.memory.remember(user_id, query, human=True)

            # Agent reasoning and execution loop
            for iteration in range(self.max_iterations):
                emit("agent", state="iteration", iteration=iteration)

                # Inject memory context into state for reasoning
                if self.memory:
                    # Temporarily enhance state with memory context
                    memory_context = await self.memory.activate(user_id)
                    original_context = state.context

                    def enhanced_context(mc=memory_context, oc=original_context):
                        return f"{mc}\n\n{oc()}" if mc else oc()

                    state.context = enhanced_context

                # Reason: What should I do next?
                reasoning = await reason(state, self.llm, self.tools, identity or self.identity)

                # Restore original context method
                if self.memory:
                    state.context = original_context

                if reasoning.get("response"):
                    # Direct response - we're done
                    response = reasoning["response"]
                    break

                actions = reasoning.get("actions", [])
                if actions:
                    # Act on reasoning decisions
                    await act(actions, self.tools, state)

                    # Continue ReAct loop - let LLM decide if task is complete
                    # Tool results are stored in state for next reasoning iteration
                    continue
                # No actions and no response - shouldn't happen with proper reasoning
                response = "Unable to determine next steps for this request."
                break
            else:
                # Max iterations reached
                response = f"Task processed through {self.max_iterations} iterations."

            # Learn from response
            if self.memory and response:
                await self.memory.remember(user_id, response, human=False)

            # Domain-specific learning operations - canonical boundaries
            from cogency.knowledge import extract
            from cogency.memory import learn

            if self.memory:
                await learn(state, self.memory)  # Learn user patterns

                # Only extract knowledge from substantial conversations
                if self._should_extract_knowledge(query, response, state):
                    await extract(state, self.memory)  # Extract knowledge

            emit("agent", state="complete", response_length=len(response))
            return response

        except Exception as e:
            emit("agent", state="error", error=str(e))
            return f"Error: {str(e)}"

    def _should_extract_knowledge(self, query: str, response: str, state) -> bool:
        """Determine if conversation is substantial enough for knowledge extraction."""
        # Skip very short interactions
        if len(query) < 20 or len(response) < 50:
            return False

        # Skip simple greetings and basic questions
        query_lower = query.lower().strip()
        simple_patterns = [
            "hello",
            "hi",
            "hey",
            "thanks",
            "thank you",
            "what time",
            "what's the weather",
            "what day",
            "who are you",
            "what are you",
            "how are you",
        ]

        if any(pattern in query_lower for pattern in simple_patterns):
            return False

        # Skip if no tools were used (likely simple factual exchange)
        if hasattr(state.execution, "completed_calls") and not state.execution.completed_calls:
            # Allow extraction for complex conceptual discussions even without tools
            return bool(len(query) > 100 or len(response) > 200)

        # Extract knowledge from substantial tool-assisted conversations
        return True

    def logs(
        self,
        *,
        type: str = None,
        errors_only: bool = False,
        last: int = None,
    ) -> list[dict[str, Any]]:
        """Get execution logs with optional filtering."""
        from cogency.events import get_logs

        return get_logs(type=type, errors_only=errors_only, last=last)


__all__ = ["Agent"]
