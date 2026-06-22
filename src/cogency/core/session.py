"""Shared setup for replay and resume execution modes."""

import logging
from typing import Literal

from cogency import context
from cogency.core.accumulator import Accumulator
from cogency.core.config import Config
from cogency.lib.metrics import Metrics

logger = logging.getLogger(__name__)


class Session:
    """Pre-built execution context shared by replay and resume."""

    __slots__ = ("accumulator", "config", "conversation_id", "messages", "metrics", "user_id")

    def __init__(
        self,
        messages: list[dict],
        metrics: Metrics | None,
        accumulator: Accumulator,
        config: Config,
        conversation_id: str,
        user_id: str,
    ):
        self.messages = messages
        self.metrics = metrics
        self.accumulator = accumulator
        self.config = config
        self.conversation_id = conversation_id
        self.user_id = user_id


async def setup(
    query: str,
    user_id: str | None,
    conversation_id: str,
    *,
    config: Config,
    stream: Literal["event", "token", None] = "event",
) -> Session:
    """Assemble context, wire notifications, init metrics+accumulator."""
    model_name = getattr(config.llm, "http_model", "unknown")
    metrics = Metrics.init(model_name)

    messages = await context.assemble(
        user_id or "",
        conversation_id,
        tools=config.tools,
        storage=config.storage,
        history_window=config.history_window,
        history_transform=config.history_transform,
        profile_enabled=config.profile,
        identity=config.identity,
        instructions=config.instructions,
    )

    if config.notifications:
        try:
            pending = await config.notifications()
            for notification in pending:
                messages.append({"role": "system", "content": notification})
        except Exception as e:
            logger.warning(f"Notification source failed: {e}")

    if metrics:
        metrics.start_step()
        metrics.add_input(messages)

    token_streaming = stream == "token"
    accumulator = Accumulator(
        user_id or "",
        conversation_id,
        execution=config.execution,
        stream="token" if token_streaming else "event",
    )

    return Session(
        messages=messages,
        metrics=metrics,
        accumulator=accumulator,
        config=config,
        conversation_id=conversation_id,
        user_id=user_id or "",
    )
