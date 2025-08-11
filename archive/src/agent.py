"""Cognitive agent with zero ceremony."""

from typing import Any, Union

from cogency.config.validation import validate_config_keys
from cogency.memory.situate import situate
from cogency.setup import AgentSetup
from cogency.steps.act import act
from cogency.steps.execution import execute_agent
from cogency.steps.reason import reason
from cogency.steps.triage import triage
from cogency.tools import Tool
from cogency.utils.validation import validate_query


class Agent:
    """Cognitive agent with zero ceremony.

    Args:
        name: Agent identifier (default "cogency")
        tools: Tools to enable - list of names, Tool objects, or single string
        memory: Enable memory - True for defaults or SituatedMemory instance for custom
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
        Advanced: Agent("assistant", memory=SituatedMemory(provider, store))
    """

    def __init__(
        self,
        name: str = "cogency",
        *,
        tools: Union[list[str], list[Tool], str] = None,
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
            **config,  # Apply user overrides
        )

        # Setup events system
        AgentSetup.events(agent_config)

        # Setup components directly - no Runtime/Executor ceremony
        self.llm = AgentSetup.llm(agent_config.llm)
        self.embed = AgentSetup.embed(agent_config.embed)

        # CANONICAL: Direct dependency injection - no global state mutations
        self.tools = AgentSetup.tools(agent_config.tools, self.embed)
        persistence = AgentSetup.persistence(agent_config.persist)
        self.memory = AgentSetup.memory(agent_config.memory, self.llm, persistence, self.embed)
        self.max_iterations = agent_config.max_iterations
        self.identity = agent_config.identity or ""

    def get_memory(self):
        """Access memory component."""
        return self.memory

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
        from resilient_result import Result

        from cogency.events import emit
        from cogency.state import State
        from cogency.state.mutations import add_message

        try:
            # Input validation
            error = validate_query(query)
            if error:
                raise ValueError(error)

            # Setup execution state - Option A+: immediate persistence
            state = State(query=query, user_id=user_id)

            # Prepare query
            wrapped_query = f"[user]\n{query.strip()}\n[/user]"
            add_message(state, "user", wrapped_query)

            # Memory operations
            if self.memory:
                await self.memory.load(user_id)
                await self.memory.remember(query, human=True)

                # Initialize archival memory (singleton handles this)
                # No ceremony - archive singleton is already configured

                # Connect memory to state
                user_profile = await self.memory._load_profile(user_id)
                if user_profile:
                    # Copy user profile data into state
                    state.preferences = user_profile.preferences
                    state.goals = user_profile.goals
                    state.expertise = user_profile.expertise
                    state.communication_style = user_profile.communication_style
                    state.projects = user_profile.projects

            # Set agent mode
            state.mode = "adapt"

            # Execute - direct functional composition, no Executor ceremony
            emit("start", query=query)

            await execute_agent(
                state,
                lambda s: triage(s, llm=self.llm, tools=self.tools, memory=self.memory),
                lambda s: reason(
                    s,
                    llm=self.llm,
                    tools=self.tools,
                    memory=self.memory,
                    identity=identity or self.identity,
                ),
                lambda s: act(s, llm=self.llm, tools=self.tools),
                lambda s: situate(s, self.memory),
                self.memory,
            )

            # Extract response
            response = state.execution.response

            # Unwrap Result objects
            if isinstance(response, Result):
                response = response.data if response.success else None

            # Learn from response
            if self.memory and response:
                await self.memory.remember(response, human=False)

            return response or "No response generated"

        except ValueError as e:
            return str(e)
        except Exception as e:
            import traceback

            error_msg = f"Flow execution failed: {e}\n{traceback.format_exc()}"
            emit("error", message=error_msg)
            raise e

    async def stream(self, query: str, user_id: str = "default", identity: str = None):
        """Stream agent response asynchronously.

        Args:
            query: User query to process
            user_id: User identifier for memory/state
            identity: Override agent identity for this query

        Yields:
            Agent response chunks
        """
        # For now, just return the full response - streaming can be enhanced later
        response = await self.run_async(query, user_id, identity)
        yield response

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
