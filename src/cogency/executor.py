"""Pure agent execution - explicit dependencies, zero setup."""

from typing import Optional

from cogency.persist.utils import _get_state
from cogency.state import AgentMode
from cogency.steps.composition import _setup_steps
from cogency.steps.execution import execute_agent
from cogency.utils.validation import validate_query


class AgentExecutor:
    """Pure execution engine - explicit dependencies, no setup magic."""

    def __init__(
        self,
        llm,
        tools,
        memory,
        config,
        max_iterations=10,
        identity="",
        output_schema=None,
        persistence=None,
    ):
        """Explicit dependency injection - no hiding."""
        self.llm = llm
        self.tools = tools
        self.memory = memory
        self.config = config
        self.persistence = persistence
        self.max_iterations = max_iterations
        self.identity = identity
        self.output_schema = output_schema

        # Setup execution steps
        self.steps = _setup_steps(
            self.llm, self.tools, self.memory, self.identity, self.output_schema, self.config
        )

        # Runtime state
        self.user_states = {}
        self.last_state: Optional[dict] = None

    async def run(self, query: str, user_id: str = "default", identity: str = None) -> str:
        """Execute agent with explicit flow."""
        from resilient_result import Result

        from cogency.events import emit

        try:
            # Input validation
            error = validate_query(query)
            if error:
                raise ValueError(error)

            # Setup execution state
            state = await _get_state(
                user_id,
                query,
                self.max_iterations,
                self.user_states,
                self.persistence,
            )

            # Prepare query
            wrapped_query = f"[user]\n{query.strip()}\n[/user]"
            state.execution.add_message("user", wrapped_query)

            # Memory operations
            if self.memory:
                await self.memory.load(user_id)
                await self.memory.remember(query, human=True)
                # Connect memory to state
                user_profile = await self.memory._load_profile(user_id)
                state.user = user_profile

            # Set agent mode
            state.execution.mode = AgentMode.ADAPT

            # Use runtime identity if provided
            steps = self.steps
            if identity:
                steps = _setup_steps(
                    self.llm, self.tools, self.memory, identity, self.output_schema, self.config
                )

            # Execute
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
        """Stream agent execution with real-time updates."""
        from cogency.events import emit

        try:
            error = validate_query(query)
            if error:
                yield f"Error: {error}"
                return

            state = await _get_state(
                user_id, query, self.max_iterations, self.user_states, self.persistence
            )

            wrapped_query = f"[user]\n{query.strip()}\n[/user]"
            state.execution.add_message("user", wrapped_query)

            if self.memory:
                await self.memory.load(user_id)
                await self.memory.remember(query, human=True)
                user_profile = await self.memory._load_profile(user_id)
                state.user = user_profile

            state.execution.mode = AgentMode.ADAPT

            steps = self.steps
            if identity:
                steps = _setup_steps(
                    self.llm, self.tools, self.memory, identity, self.output_schema, self.config
                )

            emit("start", query=query)

            # Execute with streaming via event handlers
            await execute_agent(
                state,
                steps["triage"],
                steps["reason"],
                steps["act"],
                steps["respond"],
                steps["synthesize"],
            )

            self.last_state = state
            response = state.execution.response

            if self.memory and response:
                await self.memory.remember(response, human=False)

            yield response or "No response generated"

        except Exception as e:
            yield f"Error: {str(e)}"
