"""Streaming agent with stateless context assembly.

Usage:
  agent = Agent(llm="openai")
  async for event in agent(query):
      if event["type"] == "respond":
          result = event["content"]
"""

import asyncio
import logging
from typing import Literal

import anthropic
import google.api_core.exceptions
import google.genai
import httpx
import openai

from .. import context
from ..lib import llms
from ..lib.sqlite import default_storage
from ..tools import tools as default_tools
from . import replay, resume
from .config import Config, Security
from .errors import ConfigError, LLMError
from .protocols import LLM, HistoryTransform, NotificationSource, Storage, Tool

logger = logging.getLogger(__name__)


class Agent:
    """Agent with a clear, explicit, and immutable configuration.

    The Agent is the primary interface for interacting with the Cogency framework.
    Its constructor is the single point of configuration, providing a self-documenting
    and type-safe way to set up agent behavior.

    Usage:
      agent = Agent(llm="openai", storage=default_storage())
      async for event in agent("What is the capital of France?"):
          print(event)

    Concurrency:
      - Agent instances are immutable (safe to share across calls/threads)
      - Multiple calls to same agent instance: safe
      - Same conversation_id from multiple processes: undefined (SQLite WAL single-writer limit)
    """

    def __init__(
        self,
        llm: str | LLM,
        storage: Storage | None = None,
        *,
        identity: str | None = None,
        instructions: str | None = None,
        tools: list[Tool] | None = None,
        mode: str = "auto",
        max_iterations: int = 10,
        history_window: int | None = None,
        history_transform: HistoryTransform | None = None,
        profile: bool = False,
        security: Security | None = None,
        debug: bool = False,
        notifications: NotificationSource | None = None,
    ):
        """Initializes the Agent with an explicit configuration.

        Args:
            llm: An LLM instance or a string identifier (e.g., "openai", "gemini").
            storage: A Storage implementation. Defaults to local file-based storage.
            identity: Core agent identity (who you are). Overrides default Cogency identity.
            instructions: Additional instructions to steer the agent's behavior.
            tools: A list of Tool instances. Defaults to a standard set.
            mode: Coordination mode ("auto", "resume", "replay"). Defaults to "auto".
            max_iterations: Maximum number of execution iterations.
            history_window: Number of historical events to include in context (None = full history).
            history_transform: Optional callable to transform/compress conversation history.
            profile: Enable automatic profile learning. Defaults to False.
            security: A Security object defining access levels and timeouts.
            debug: Enable verbose debug logging.
            notifications: Notification source for mid-execution context injection.
        """
        if debug:
            logging.getLogger("cogency").setLevel(logging.DEBUG)

        final_security = security or Security()
        final_storage = storage or default_storage()
        final_tools = default_tools() if tools is None else tools
        final_llm = llms.create(llm) if isinstance(llm, str) else llm

        self.config = Config(
            llm=final_llm,
            storage=final_storage,
            tools=final_tools,
            identity=identity,
            instructions=instructions,
            mode=mode,
            max_iterations=max_iterations,
            history_window=history_window,
            history_transform=history_transform,
            profile=profile,
            security=final_security,
            debug=debug,
            notifications=notifications,
        )

        valid_modes = ["auto", "resume", "replay"]
        if self.config.mode not in valid_modes:
            raise ConfigError(f"mode must be one of {valid_modes}, got: {self.config.mode}")

    async def __call__(
        self,
        query: str,
        user_id: str | None = None,
        conversation_id: str | None = None,
        stream: Literal["event", "token", None] = "event",
    ):
        """Stream events for query.

        Args:
            query: User query
            user_id: User identifier (None = no profile)
            conversation_id: Conversation identifier (None = stateless/ephemeral)
            stream: Streaming strategy. "token" yields chunks as they arrive,
                   "event" accumulates and yields complete semantic units,
                   None uses LLM.generate() for non-streaming response.
                   Defaults to "event".
        """
        try:
            import time

            # Generate ephemeral ID for iteration continuity if none provided
            if conversation_id is None:
                import uuid

                conversation_id = str(uuid.uuid4())

            # Persist user message once at agent entry
            timestamp = time.time()
            await self.config.storage.save_message(
                conversation_id, user_id or "", "user", query, timestamp
            )

            # Emit user event - first event in conversation turn
            yield {"type": "user", "content": query, "timestamp": timestamp}

            storage = self.config.storage

            if self.config.mode == "resume":
                mode_stream = resume.stream
            elif self.config.mode == "auto":
                # Try resume first, fall back to replay on failure
                try:
                    async for event in resume.stream(
                        query,
                        user_id,
                        conversation_id,
                        config=self.config,
                        stream=stream,
                    ):
                        yield event
                    # Trigger profile learning if enabled
                    if self.config.profile:
                        context.learn(
                            user_id,
                            profile_enabled=self.config.profile,
                            storage=storage,
                            llm=self.config.llm,
                        )
                    return
                except (
                    LLMError,
                    RuntimeError,
                    ValueError,
                    AttributeError,
                    httpx.RequestError,
                ) as e:
                    logger.debug(f"Resume unavailable, falling back to replay: {e}")
                    mode_stream = replay.stream
            else:
                mode_stream = replay.stream

            async for event in mode_stream(
                query,
                user_id,
                conversation_id,
                config=self.config,
                stream=stream,
            ):
                yield event

            # Trigger profile learning if enabled
            if self.config.profile:
                context.learn(
                    user_id,
                    profile_enabled=self.config.profile,
                    storage=storage,
                    llm=self.config.llm,
                )
        except (KeyboardInterrupt, asyncio.CancelledError):
            import time

            timestamp = time.time()
            await self.config.storage.save_message(
                conversation_id or "", user_id or "", "cancelled", "", timestamp
            )
            yield {"type": "cancelled", "timestamp": timestamp}
        except (
            anthropic.APIError,
            openai.APIError,
            google.api_core.exceptions.GoogleAPIError,
            httpx.RequestError,
            ValueError,  # For API key not found
            RuntimeError,
        ) as e:
            logger.error(f"LLM error: {type(e).__name__}: {e}", exc_info=True)
            raise LLMError(f"LLM error: {e}", cause=e) from e
