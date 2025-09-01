"""Stream orchestration with mode selection and persistence."""

import time

from . import replay, resume
from .protocols import Event


async def stream(
    config, query: str, user_id: str, conversation_id: str, on_complete=None, on_learn=None
):
    """Stream orchestration with immediate persistence and learning callbacks.

    Parser handles DB writes via callbacks, stream manages mode selection.
    """
    # Record initial user message
    user_event = {"type": Event.USER, "content": query, "timestamp": time.time()}
    events = [user_event]

    # Record user message immediately with resilience
    if on_complete:
        from ..lib.resilience import resilient_save

        resilient_save(conversation_id, user_id, Event.USER, query, user_event["timestamp"])

    try:
        # Transport selection: WebSocket streaming → HTTP fallback → error
        if config.mode == "resume":
            mode_func = resume.stream
        elif config.mode == "auto":
            # Auto: resume when available, replay fallback
            mode_func = (
                resume.stream
                if hasattr(config.llm, "resumable") and config.llm.resumable
                else replay.stream
            )
        else:  # replay
            mode_func = replay.stream

        # Execute with immediate DB writes handled by parser
        async for event in mode_func(config, query, user_id, conversation_id):
            # Always yield for API consumers
            yield event

            # Track events for final callback
            if event["type"] == Event.RESULTS:
                events.append(event)

    finally:
        # Final callback for remaining coordination
        if on_complete:
            on_complete(conversation_id, user_id, events)

        # Learning callback (fire and forget)
        if on_learn:
            on_learn(user_id, config.llm)


__all__ = ["stream"]
