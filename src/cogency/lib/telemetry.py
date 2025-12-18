import asyncio
import json
import logging
from typing import Any

from cogency.core.protocols import Event, Storage

logger = logging.getLogger(__name__)


def add_event(events_list: list[Event], event: Event):
    events_list.append(event)


async def persist_events(conversation_id: str, events_list: list[Event], storage: Storage):
    if not events_list:
        return

    try:
        tasks: list[Any] = []
        for event in events_list:
            content = event.get("content", "")
            if isinstance(content, dict):
                content = json.dumps(content)

            tasks.append(
                storage.save_event(
                    conversation_id=conversation_id,
                    type=str(event["type"]),
                    content=str(content),
                )
            )
        await asyncio.gather(*tasks)
        logger.debug(f"Persisted telemetry for {conversation_id}: {json.dumps(events_list)}")
        events_list.clear()
    except Exception as exc:
        logger.error(f"Failed to persist telemetry for {conversation_id}: {exc}")
