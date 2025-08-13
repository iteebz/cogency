"""State-driven event orchestration for canonical observability."""

import functools
from typing import Any, Callable, TypeVar

from .bus import emit

F = TypeVar("F", bound=Callable[..., Any])


def state_event(
    event_type: str, extract_data: Callable[..., dict] | None = None
) -> Callable[[F], F]:
    """Decorator to emit events from state mutations canonically.

    Args:
        event_type: Type of event to emit (e.g., "conversation_saved")
        extract_data: Function to extract event data from method args/result
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Execute state mutation
            result = await func(*args, **kwargs)

            # Only emit event if mutation succeeded
            if result:
                event_data = {}
                if extract_data:
                    event_data = extract_data(args, kwargs, result)

                # Canonical event emission tied to state change
                emit(event_type, level="debug", success=True, **event_data)
            else:
                # Emit failure event for observability
                emit(event_type, level="debug", success=False)

            return result

        return wrapper

    return decorator


def extract_conversation_data(args, kwargs, result) -> dict:
    """Extract conversation event data from save_conversation args."""
    conversation = args[1] if len(args) > 1 else kwargs.get("conversation")
    if conversation:
        return {
            "conversation_id": conversation.conversation_id,
            "user_id": conversation.user_id,
            "message_count": len(conversation.messages),
        }
    return {}


def extract_profile_data(args, kwargs, result) -> dict:
    """Extract profile event data from save_profile args."""
    state_key = args[1] if len(args) > 1 else kwargs.get("state_key")
    profile = args[2] if len(args) > 2 else kwargs.get("profile")

    data = {"state_key": state_key}
    if profile and hasattr(profile, "user_id"):
        data["user_id"] = profile.user_id

    return data


def extract_workspace_data(args, kwargs, result) -> dict:
    """Extract workspace event data from save_workspace args."""
    # save_workspace(self, task_id, user_id, workspace)
    task_id = args[1] if len(args) > 1 else kwargs.get("task_id")
    user_id = args[2] if len(args) > 2 else kwargs.get("user_id")
    workspace = args[3] if len(args) > 3 else kwargs.get("workspace")

    data = {}
    if task_id:
        data["task_id"] = task_id
    if user_id:
        data["user_id"] = user_id
    if workspace and hasattr(workspace, "conversation_id"):
        data["conversation_id"] = workspace.conversation_id

    return data


def extract_knowledge_data(args, kwargs, result) -> dict:
    """Extract knowledge event data from save_knowledge args."""
    artifact = args[1] if len(args) > 1 else kwargs.get("artifact")
    if artifact:
        return {
            "topic": artifact.topic,
            "user_id": artifact.user_id,
            "content_type": artifact.content_type,
        }
    return {}


def extract_delete_data(args, kwargs, result) -> dict:
    """Extract deletion event data from delete methods."""
    # Most delete methods take an ID as first argument after self
    if len(args) > 1:
        return {"target_id": args[1]}
    return {}
