"""Streaming agents - pure stream protocol.

Usage:
  agent = Agent()              # Configuration closure
  async for event in agent(query):  # Returns event stream
      if event["type"] == "respond":
          result = event["content"]
"""

from ..context import context
from ..lib.logger import logger
from ..lib.storage import SQLite
from ..tools import TOOLS
from .config import Config
from .protocols import LLM, Event, Mode, Storage
from .stream import stream


class Agent:
    """Agent as configuration closure - stateless execution."""

    def __init__(
        self,
        llm: str | LLM = "gemini",
        storage: Storage | None = None,
        tools: list | None = None,
        instructions: str | None = None,
        mode: str = "auto",
        max_iterations: int = 3,
        profile: bool = True,
        sandbox: bool = True,
    ):
        # Build internal config from parameters - single source of truth
        # Agent(llm="gemini") is better DX than Agent(Config(llm="gemini"))
        # Config is internal data structure, not user-facing API
        self.config = Config(
            llm=self._create_llm(llm),
            storage=storage or SQLite(),
            tools=tools if tools is not None else TOOLS,
            instructions=instructions,
            mode=mode,
            max_iterations=max_iterations,
            profile=profile,
            sandbox=sandbox,
        )

        # Validate mode during construction
        try:
            Mode(mode)
        except ValueError:
            valid_modes = [m.value for m in Mode]
            raise ValueError(f"mode must be one of {valid_modes}, got: {mode}") from None

        # Stateless - agent is pure function with configuration closure

    def _create_llm(self, llm) -> LLM:
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

    async def __call__(
        self, query: str, user_id: str = "default", conversation_id: str | None = None
    ):
        """Stream events for query - pure streaming protocol."""
        conversation_id = conversation_id or f"{user_id}_session"

        try:
            # Bind recording function to agent's storage with resilience
            def record_to_storage(conversation_id: str, user_id: str, events: list) -> bool:
                try:
                    return self.config.storage.record_message(conversation_id, user_id, events)
                except Exception as e:
                    logger.debug(f"Storage recording failed: {e}")
                    return False  # Graceful degradation

            async for event in stream(
                self.config,
                query,
                user_id,
                conversation_id,
                on_complete=record_to_storage,
                on_learn=context.learn,
            ):
                yield event
        except Exception as e:
            logger.debug(f"Stream failed: {e}")
            raise RuntimeError("Stream failed") from None  # [SEC-003] No error chain leakage
