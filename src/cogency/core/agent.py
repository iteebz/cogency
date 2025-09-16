"""Streaming agent with stateless context assembly.

Usage:
  agent = Agent()
  async for event in agent(query):
      if event["type"] == "respond":
          result = event["content"]
"""

from .. import context
from ..lib.storage import default_storage
from ..tools import TOOLS
from . import replay, resume
from .config import Config
from .protocols import LLM


class Agent:
    """Agent with immutable configuration and fresh context assembly per call."""

    def __init__(self, llm: str | LLM = "gemini", **kwargs):
        if kwargs.pop("debug", False):
            from ..lib.logger import set_debug

            set_debug(True)

        # Handle special processing for some fields, but keep in kwargs for Config
        if "tools" not in kwargs:
            kwargs["tools"] = TOOLS
        if "storage" not in kwargs:
            kwargs["storage"] = default_storage()
        
        self.config = Config(
            llm=self._create_llm(llm),
            **kwargs,  # All fields pass through to Config
        )

        # Validate mode during construction
        valid_modes = ["auto", "resume", "replay"]
        if self.config.mode not in valid_modes:
            raise ValueError(f"mode must be one of {valid_modes}, got: {self.config.mode}")

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

            if self.config.mode == "resume":
                mode_stream = resume.stream
            elif self.config.mode == "auto":
                # Try resume first, fall back to replay on failure
                try:
                    async for event in resume.stream(
                        self.config, query, user_id, conversation_id, chunks
                    ):
                        yield event
                    # Trigger profile learning if enabled
                    if self.config.profile:
                        context.learn(user_id, self.config)
                    return
                except Exception as e:
                    from ..lib.logger import logger

                    logger.debug(f"Resume failed, falling back to replay: {e}")
                    mode_stream = replay.stream
            else:
                mode_stream = replay.stream

            async for event in mode_stream(self.config, query, user_id, conversation_id, chunks):
                yield event

            # Trigger profile learning if enabled
            if self.config.profile:
                context.learn(user_id, self.config)
        except Exception as e:
            from ..lib.logger import logger

            logger.error(f"Stream execution failed: {type(e).__name__}: {e}")
            raise RuntimeError(
                f"Stream execution failed: {type(e).__name__}"
            ) from None  # [SEC-003] No error chain leakage
