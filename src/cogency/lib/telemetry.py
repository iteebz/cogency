import json

from ..lib.logger import logger


def add_event(events_list: list[dict], event: dict):
    events_list.append(event)


def persist_events(conversation_id: str, events_list: list[dict]):
    if not events_list:
        return

    try:
        # In a real system, this would persist to a database or external service.
        # For now, we'll just log it.
        logger.debug(f"Persisting telemetry for {conversation_id}: {json.dumps(events_list)}")
        events_list.clear()
    except Exception as exc:
        logger.debug(f"Failed to persist telemetry for {conversation_id}: {exc}")
