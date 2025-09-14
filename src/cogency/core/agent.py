"""Streaming agents - pure stream protocol.

Usage:
  agent = Agent()              # Configuration closure
  async for event in agent(query):  # Returns event stream
      if event["type"] == "respond":
          result = event["content"]
"""

from ..context import context
from ..lib.logger import logger
from ..lib.storage import default_storage
from ..tools import TOOLS
from . import replay, resume
from .config import Config
from .protocols import LLM, Storage


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
            storage=storage or default_storage(),
            tools=tools if tools is not None else TOOLS,
            instructions=instructions,
            mode=mode,
            max_iterations=max_iterations,
            profile=profile,
            sandbox=sandbox,
        )

        # Validate mode during construction
        valid_modes = ["auto", "resume", "replay"]
        if mode not in valid_modes:
            raise ValueError(f"mode must be one of {valid_modes}, got: {mode}")

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
        self,
        query: str,
        user_id: str = "default",
        conversation_id: str | None = None,
        chunks: bool = False,
    ):
        """Stream events for query.

        Args:
            query: User query
            user_id: User identifier
            conversation_id: Conversation identifier
            chunks: If True, stream individual tokens. If False, stream semantic events.
        """
        conversation_id = conversation_id or f"{user_id}_session"

        try:
            # Explicit storage handling - no silent failures
            async def finalize_storage(conversation_id: str, user_id: str, events: list):
                try:
                    await self.config.storage.record_message(conversation_id, user_id, events)
                    logger.debug("Conversation saved successfully")
                except Exception as e:
                    logger.warning(f"Cannot save conversation: {e}")
                    # Notify but continue - user knows storage is unavailable

            # Mode selection - no orchestrator needed
            if self.config.mode == "resume":
                mode_stream = resume.stream
            elif self.config.mode == "auto":
                # Try WebSocket first, fallback to HTTP on any failure
                try:
                    mode_stream = resume.stream
                except Exception:
                    mode_stream = replay.stream
            else:
                mode_stream = replay.stream

            async for event in mode_stream(self.config, query, user_id, conversation_id, chunks):
                yield event

            # Post-stream callbacks
            await finalize_storage(conversation_id, user_id, [])
            context.learn(user_id, self.config.llm)
        except Exception as e:
            logger.debug(f"Stream failed: {e}")
            raise RuntimeError("Stream failed") from None  # [SEC-003] No error chain leakage
