"""Task operations - domain-centric task lifecycle.

Replaces State.start_task() with direct domain primitive operations.
No container object - just returns domain primitives directly.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .session import TaskSession
from .conversation import create_conversation, load_conversation
from .working import create_working_state
from .execution import create_execution

if TYPE_CHECKING:
    from cogency.storage.sqlite import SQLite
    from .conversation import Conversation
    from .working import WorkingState
    from .execution import Execution


async def start_task(
    query: str,
    user_id: str = "default", 
    conversation_id: str = None,
    max_iterations: int = 10,
    store: "SQLite" = None,
) -> tuple["TaskSession", "Conversation", "WorkingState", "Execution"]:
    """Start new task with domain primitives - no State container.
    
    Returns domain primitives directly for agent to coordinate.
    """
    if store is None:
        from cogency.storage.sqlite import SQLite
        store = SQLite()
    
    # Create coordination metadata
    session = TaskSession(
        query=query,
        user_id=user_id,
        conversation_id=conversation_id,
    )
    
    # Load or create conversation domain
    if conversation_id:
        conversation = await load_conversation(conversation_id, user_id, store)
        if conversation is None:
            raise ValueError(f"No conversation found for conversation_id: {conversation_id}")
    else:
        conversation = await create_conversation(user_id, store)
        session.conversation_id = conversation.conversation_id
    
    # Create working state domain
    working_state = create_working_state(query)
    
    # Create execution domain
    execution = create_execution(max_iterations)
    
    # Load conversation history into execution for LLM context
    from .conversation import get_messages_for_llm
    execution.messages = get_messages_for_llm(conversation)
    
    # Save working state
    from .working import save_working_state
    await save_working_state(session.task_id, session.user_id, working_state, store)
    
    return session, conversation, working_state, execution


async def continue_task(
    task_id: str,
    user_id: str = "default",
    max_iterations: int = 10,
    store: "SQLite" = None,
) -> tuple["TaskSession", "Conversation", "WorkingState", "Execution"]:
    """Resume existing task with preserved domain state."""
    if store is None:
        from cogency.storage.sqlite import SQLite
        store = SQLite()
    
    # Load working state
    from .working import load_working_state
    working_state = await load_working_state(task_id, user_id, store)
    if working_state is None:
        raise ValueError(f"No working state found for task_id: {task_id}")
    
    # Create session from working state
    session = TaskSession(
        query=working_state.objective,
        user_id=user_id,
        task_id=task_id,
    )
    
    # Create empty conversation (TODO: link conversation_id to working state)
    conversation = await create_conversation(user_id, store)
    
    # Create fresh execution
    execution = create_execution(max_iterations)
    
    return session, conversation, working_state, execution


__all__ = ["start_task", "continue_task"]