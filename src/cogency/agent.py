"""Streaming agent. Usage: async for event in Agent(llm="openai")(query): ..."""

import asyncio
import logging
import time
import uuid
from typing import Literal

import anthropic
import google.api_core.exceptions
import httpx
import openai

from . import context, replay, resume
from .core.config import Config, Security
from .core.errors import ConfigError, LLMError
from .core.protocols import (
    LLM,
    CancelledEvent,
    HistoryTransform,
    NotificationSource,
    Storage,
    Tool,
    UserEvent,
)
from .lib import llms
from .lib.sqlite import default_storage
from .tools import tools as builtin_tools

logger = logging.getLogger(__name__)


async def _select_mode_stream(
    mode: str,
    config: Config,
    query: str,
    user_id: str | None,
    conversation_id: str,
    stream: Literal["event", "token", None],
):
    """Select and attempt streaming mode with auto-fallback."""
    if mode == "resume":
        async for event in resume.stream(
            query, user_id, conversation_id, config=config, stream=stream
        ):
            yield event
    elif mode == "auto":
        try:
            async for event in resume.stream(
                query, user_id, conversation_id, config=config, stream=stream
            ):
                yield event
        except (LLMError, RuntimeError, ValueError, httpx.RequestError) as e:
            logger.debug(f"Resume unavailable, falling back to replay: {e}")
            async for event in replay.stream(
                query, user_id, conversation_id, config=config, stream=stream
            ):
                yield event
    else:
        async for event in replay.stream(
            query, user_id, conversation_id, config=config, stream=stream
        ):
            yield event


class Agent:
    """Immutable agent configuration.

    Concurrency:
    - Thread-safe: instances immutable, safe to share
    - Process-safe: multiple readers OK, concurrent writes to same conversation_id undefined
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
        profile_cadence: int = 5,
        security: Security | None = None,
        debug: bool = False,
        notifications: NotificationSource | None = None,
    ):
        if debug:
            logging.getLogger("cogency").setLevel(logging.DEBUG)

        final_security = security or Security()
        final_storage = storage or default_storage()
        final_tools = builtin_tools() if tools is None else tools
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
            profile_cadence=profile_cadence,
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
        try:
            # Generate ephemeral ID for iteration continuity if none provided
            if conversation_id is None:
                conversation_id = str(uuid.uuid4())

            # Persist user message once at agent entry
            timestamp = time.time()
            await self.config.storage.save_message(
                conversation_id, user_id or "", "user", query, timestamp
            )

            # Emit user event - first event in conversation turn
            yield UserEvent(type="user", content=query, timestamp=timestamp)

            async for event in _select_mode_stream(
                self.config.mode, self.config, query, user_id, conversation_id, stream
            ):
                yield event

            if self.config.profile:
                context.learn(
                    user_id,
                    profile_enabled=self.config.profile,
                    storage=self.config.storage,
                    llm=self.config.llm,
                    cadence=self.config.profile_cadence,
                )
        except (KeyboardInterrupt, asyncio.CancelledError):
            timestamp = time.time()
            await self.config.storage.save_message(
                conversation_id or "", user_id or "", "cancelled", "", timestamp
            )
            yield CancelledEvent(type="cancelled", timestamp=timestamp)
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
