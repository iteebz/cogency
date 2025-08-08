"""Clean agent runtime - coordination only."""

from typing import Any

from cogency.executor import AgentExecutor
from cogency.setup import AgentSetup


class AgentRuntime:
    """Clean coordination layer - setup → execution."""

    def __init__(self, config):
        self.name = config.name
        self._initialized = True

        # Setup events system
        AgentSetup.events(config)

        # Setup components explicitly
        agent_config = AgentSetup.config(config)
        llm = AgentSetup.llm(config.llm)
        tools = AgentSetup.tools(config.tools)
        persistence = AgentSetup.persistence(True)
        memory = AgentSetup.memory(config.memory, llm, persistence)

        # Create executor with explicit dependencies
        self.executor = AgentExecutor(
            llm=llm,
            tools=tools,
            memory=memory,
            config=agent_config,
            max_iterations=config.max_iterations,
            identity=config.identity or "",
            output_schema=config.output_schema,
            persistence=persistence,
        )

    async def cleanup(self):
        """Clean up resources."""
        if not self._initialized:
            return

        from cogency.events import emit

        try:
            emit("agent_teardown", name=self.name, status="cleaning")

            # Clear executor state
            if hasattr(self.executor, "user_states"):
                self.executor.user_states.clear()
                self.executor.last_state = None

            self._initialized = False
            emit("agent_teardown", name=self.name, status="complete")

        except Exception as e:
            emit("agent_teardown", name=self.name, status="error", error=str(e))
            raise

    @classmethod
    async def create(cls, name: str) -> "AgentRuntime":
        """Create runtime with default configuration."""
        from cogency.config.dataclasses import AgentConfig

        config = AgentConfig()
        config.name = name
        return cls(config)

    @classmethod
    async def configure(cls, config) -> "AgentRuntime":
        """Create runtime from builder config."""
        return cls(config)

    async def run(self, query: str, user_id: str = "default", identity: str = None) -> str:
        """Execute agent - delegate to executor."""
        return await self.executor.run(query, user_id, identity)

    async def stream(self, query: str, user_id: str = "default", identity: str = None):
        """Stream agent response - delegate to executor."""
        async for chunk in self.executor.stream(query, user_id, identity):
            yield chunk

    def logs(self) -> list[dict[str, Any]]:
        """Execution logs summary."""
        from cogency.events import get_logs

        return get_logs(summary=True)
