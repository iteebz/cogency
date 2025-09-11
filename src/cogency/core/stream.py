"""Stream orchestration with mode selection and persistence."""

import asyncio
import time

from . import replay, resume
from .protocols import Event, Mode


async def stream(
    config, query: str, user_id: str, conversation_id: str, on_complete=None, on_learn=None
):
    """Stream orchestration with immediate persistence and learning callbacks.

    Parser handles DB writes via callbacks, stream manages mode selection.
    """
    # Record initial user message
    user_event = {"type": Event.USER, "content": query, "timestamp": time.time()}
    events = []  # Don't include user event in final callback

    # Record user message immediately
    if on_complete:
        on_complete(conversation_id, user_id, [user_event])

    try:
        # Transport selection: WebSocket streaming → HTTP fallback → error
        mode = Mode(config.mode)

        # Mode selection with auto-fallback
        if mode == Mode.RESUME:
            mode_func = resume.stream
        elif mode == Mode.AUTO and getattr(config.llm, "resumable", False):
            # Try resume with fallback - buffer events to avoid duplication
            try:
                resume_events = []
                async for event in resume.stream(config, query, user_id, conversation_id):
                    resume_events.append(event)
                # Resume succeeded - yield all buffered events
                for event in resume_events:
                    yield event
                return
            except Exception as e:
                from ..lib.logger import logger

                logger.info(f"Resume mode failed, falling back to replay: {str(e)}")
                # Resume failed - discard buffered events, use replay
                mode_func = replay.stream
        else:
            mode_func = replay.stream

        # Execute with immediate DB writes handled by parser
        async for event in mode_func(config, query, user_id, conversation_id):
            # Always yield events for API consumers
            yield event

            # Track events for final callback
            if event["type"] in (Event.RESULTS, Event.RESPOND):
                events.append(event)

    except asyncio.CancelledError:
        # Re-raise cancellation after cleanup
        raise
    finally:
        # Final callback for remaining coordination
        if on_complete:
            on_complete(conversation_id, user_id, events)

        # Learning callback (fire and forget)
        if on_learn:
            on_learn(user_id, config.llm)


__all__ = ["stream"]
