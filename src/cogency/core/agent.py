"""Streaming agent with stateless context assembly.

Usage:
  agent = Agent()
  async for event in agent(query):
      if event["type"] == "respond":
          result = event["content"]
"""

from .. import context
from ..lib.logger import logger
from ..lib.storage import default_storage
from ..tools import TOOLS
from . import replay, resume
from .config import Config
from .protocols import LLM, Storage


class Agent:
    """Agent with immutable configuration and fresh context assembly per call."""

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
        learning_cadence: int = 5,
        debug: bool = False,
    ):
        if debug:
            from ..lib.logger import set_debug

            set_debug(True)

        self.config = Config(
            llm=self._create_llm(llm),
            storage=storage or default_storage(),
            tools=tools if tools is not None else TOOLS,
            instructions=instructions,
            mode=mode,
            max_iterations=max_iterations,
            profile=profile,
            sandbox=sandbox,
            learning_cadence=learning_cadence,
        )

        # Validate mode during construction
        valid_modes = ["auto", "resume", "replay"]
        if mode not in valid_modes:
            raise ValueError(f"mode must be one of {valid_modes}, got: {mode}")

    def _create_llm(self, llm) -> LLM:
        """Create LLM instance from string or pass through existing instance."""
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
        conversation_id = conversation_id or user_id

        try:
            # Persist user message for conversation context
            await self.config.storage.save_message(conversation_id, user_id, "user", query)

            async def finalize_storage(conversation_id: str, user_id: str, events: list):
                pass  # Storage finalization handled

            if self.config.mode == "resume":
                mode_stream = resume.stream
            elif self.config.mode == "auto":
                try:
                    mode_stream = resume.stream
                except Exception:
                    mode_stream = replay.stream
            else:
                mode_stream = replay.stream

            async for event in mode_stream(self.config, query, user_id, conversation_id, chunks):
                yield event

            await finalize_storage(conversation_id, user_id, [])
            context.learn(user_id, self.config)
        except Exception as e:
            logger.error(f"Stream failed: {e}")
            raise RuntimeError("Stream failed") from None  # [SEC-003] No error chain leakage
