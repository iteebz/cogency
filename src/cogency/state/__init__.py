"""State management - execution context and session coordination.

Agent state management - Database-as-State architecture.
Pure data + pure functions = beautiful state management.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import uuid4

from cogency.context.knowledge import extract
from cogency.memory import learn
from cogency.storage.sqlite import SQLite

# Backward compatibility imports  
from cogency.context.conversation import (
    Conversation,
    create_conversation, 
    load_conversation,
    get_messages_for_llm,
)
from cogency.context.working import (
    WorkingState,
    create_working_state,
)


@dataclass
class State:
    """Pure ephemeral execution state."""

    # Identity
    query: str
    user_id: str = "default"
    task_id: str = field(default_factory=lambda: str(uuid4()))

    # Persistent conversation history
    conversation: Conversation = None

    # Task-scoped working state
    working_state: WorkingState = None

    # Runtime-only execution state
    execution: Execution | None = None

    # Security
    security_assessment: str | None = None

    # State metadata
    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)

    @classmethod
    async def start_task(
        cls,
        query: str,
        user_id: str = "default",
        conversation_id: str = None,
        max_iterations: int = 10,
    ) -> State:
        """Create new task with fresh workspace."""
        store = SQLite()

        # Load or create conversation
        if conversation_id:
            conversation = await load_conversation(conversation_id, user_id, store)
            if conversation is None:
                raise ValueError(f"No conversation found for conversation_id: {conversation_id}")
        else:
            conversation = await create_conversation(user_id, store)

        # Create fresh working state for this task
        working_state = create_working_state(query)

        # Create runtime execution state
        execution = Execution(max_iterations=max_iterations)

        # Load conversation history into execution for context
        execution.messages = get_messages_for_llm(conversation)

        state = cls(
            query=query,
            user_id=user_id,
            conversation=conversation,
            working_state=working_state,
            execution=execution,
        )

        # Save new working state (via workspace compatibility layer)
        from cogency.context.working import save_working_state
        await save_working_state(state.task_id, state.user_id, state.working_state, store)

        return state

    async def extract_knowledge(self, memory=None) -> None:
        """Extract knowledge from conversation - canonical domain operation."""
        await extract(self, memory)

    async def learn_profile(self, memory=None) -> None:
        """Learn user profile patterns - canonical domain operation."""
        await learn(self, memory)

    @classmethod
    async def continue_task(
        cls, task_id: str, user_id: str = "default", max_iterations: int = 10
    ) -> State:
        """Resume existing task with preserved workspace."""
        store = SQLite()

        # Load existing task workspace
        workspace_data = await store.load_workspace(task_id, user_id)
        if workspace_data is None:
            raise ValueError(f"No workspace found for task_id: {task_id}")

        # TODO: Need to link conversation_id to workspace to load proper conversation
        # For now, create empty conversation - this needs conversation_id in workspace
        conversation = Conversation(user_id=user_id)

        # Create fresh runtime execution state
        execution = Execution(max_iterations=max_iterations)

        # Convert legacy workspace to working_state
        from cogency.context.working import WorkingState
        working_state = WorkingState(
            objective=workspace_data.objective,
            understanding=workspace_data.assessment,
            approach=workspace_data.approach,
            discoveries="; ".join(workspace_data.insights[-3:]) if workspace_data.insights else ""
        )
        
        return cls(
            query=workspace_data.objective,  # Extract original query from workspace
            user_id=user_id,
            task_id=task_id,
            conversation=conversation,
            working_state=working_state,
            execution=execution,
        )

    def __post_init__(self):
        """Initialize components for direct construction fallback."""
        if self.conversation is None:
            self.conversation = Conversation(user_id=self.user_id)

        if self.working_state is None:
            self.working_state = create_working_state(self.query)
        elif not self.working_state.objective:
            self.working_state.objective = self.query

        if self.execution is None:
            self.execution = Execution()

    def update_from_reasoning(self, reasoning_data: dict[str, Any]) -> None:
        """Update state from LLM reasoning response."""
        # TODO: Implement direct state updates if needed
        # For now, state updates happen through normal attribute access
        pass

    async def context(self) -> str:
        """Build system context using domain-centric approach."""
        from cogency.context.assembly import build_context
        
        # Use domain-centric context assembly
        return await build_context(
            conversation=None,  # State.context() historically excluded conversation
            working_state=self.working_state,
            execution=self.execution,
            tools=None,  # No tool registry in State.context()
            memory=None,
            user_id=self.user_id,
            query=self.query
        )

    def messages(self) -> list[dict]:
        """Get conversation messages for LLM chat interface."""
        return get_messages_for_llm(self.conversation)


# Import canonical domain classes
from cogency.context.execution import Execution


__all__ = ["Execution", "State"]
