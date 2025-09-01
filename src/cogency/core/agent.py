"""Agent interface with dual API: simple strings or streaming events.

Usage:
  agent = Agent()              # Configuration closure
  result = await agent(query)  # Aggregated response
  async for event in agent.stream(query):  # Raw event stream
"""

from typing import Optional, Union

from ..context import context
from ..lib.logger import logger
from ..lib.storage import SQLite
from ..tools import TOOLS
from .config import Config
from .protocols import LLM, Storage
from .stream import stream as consciousness_stream


class Agent:
    """Agent as configuration closure - stateless execution."""

    def __init__(
        self,
        llm: Union[str, LLM] = "gemini",
        storage: Optional[Storage] = None,
        tools: Optional[list] = None,
        instructions: Optional[str] = None,
        mode: str = "auto",
        max_iterations: int = 3,
        profile: bool = True,
        sandbox: bool = True,
    ):
        # LLM setup
        self.llm = self._create_llm(llm)
        self.storage = storage or SQLite()

        # Tool setup - tools are finalized, no dynamic injection
        self.tools = tools if tools is not None else TOOLS

        # User instructions - safe agent steering layer
        self.instructions = instructions

        # Stream mode setup
        valid_modes = {"auto", "replay", "resume"}
        if mode not in valid_modes:
            raise ValueError(f"mode must be one of {valid_modes}, got: {mode}")
        self.mode = mode

        # Config flags
        self.max_iterations = max_iterations
        self.profile = profile
        self.sandbox = sandbox

        # Logger configured globally - no parameter needed

        # Stateless - agent is pure function with configuration closure

    def _create_llm(self, llm):
        """Create LLM instance from string or pass through existing instance."""
        # If already an LLM instance, use it
        from .protocols import LLM

        if isinstance(llm, LLM):
            return llm

        # String → built-in LLM
        if llm == "gemini":
            from ..lib.llms import Gemini

            return Gemini()
        if llm == "openai":
            from ..lib.llms import OpenAI

            return OpenAI()
        if llm == "anthropic":
            from ..lib.llms import Anthropic

            return Anthropic()

        valid = ["openai", "gemini", "anthropic"]
        raise ValueError(f"Unknown LLM '{llm}'. Valid options: {', '.join(valid)}")

    def _build_config(self):
        """Build agent configuration once."""
        return Config(
            llm=self.llm,
            storage=self.storage,
            tools=self.tools,
            instructions=self.instructions,
            mode=self.mode,
            max_iterations=self.max_iterations,
            sandbox=self.sandbox,
            profile=self.profile,
        )

    def _conversation_id(self, user_id: str, conversation_id: Optional[str]) -> str:
        """Get or generate conversation ID."""
        return conversation_id or f"{user_id}_session"

    async def __call__(
        self, query: str, user_id: str = "default", conversation_id: Optional[str] = None
    ) -> str:
        # Create agent config (behavior)
        config = self._build_config()

        # Runtime params (execution context)
        conversation_id = self._conversation_id(user_id, conversation_id)

        # Execute with context isolation
        logger.debug(f"Executing: {query[:50]}...")
        logger.debug(f"Context: user={user_id}, conv={conversation_id}")

        try:
            # Collect all streaming events
            respond_events = []
            async for event in consciousness_stream(
                config,
                query,
                user_id,
                conversation_id,
                on_complete=context.record,
                on_learn=context.learn,
            ):
                if event["type"] == "respond":
                    respond_events.append(event["content"])

            # Aggregate response events
            final_response = "".join(respond_events).strip() or "Execution completed"
            logger.debug(f"Completed: {len(final_response)} chars")
            return final_response
        except Exception as e:
            logger.debug(f"Failed: {e}")
            raise RuntimeError(f"Execution failed: {e}") from e

    async def stream(
        self, query: str, user_id: str = "default", conversation_id: Optional[str] = None
    ):
        # Create agent config (behavior)
        config = self._build_config()

        # Runtime params (execution context)
        conversation_id = self._conversation_id(user_id, conversation_id)

        logger.debug(f"📍 Context: user={user_id}, conv={conversation_id}")

        try:
            async for event in consciousness_stream(
                config,
                query,
                user_id,
                conversation_id,
                on_complete=context.record,
                on_learn=context.learn,
            ):
                yield event
        except Exception as e:
            logger.debug(f"Stream failed: {e}")
            raise RuntimeError(f"Stream failed: {e}") from e
