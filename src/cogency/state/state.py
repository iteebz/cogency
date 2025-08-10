"""State class with lifecycle management."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict
from uuid import uuid4

if TYPE_CHECKING:
    from . import Conversation, Execution, Profile, Workspace


@dataclass
class State:
    """Agent state with layered persistence."""

    # Identity
    query: str
    user_id: str = "default"
    task_id: str = field(default_factory=lambda: str(uuid4()))

    # Persistent user profile
    profile: Profile = None

    # Persistent conversation history
    conversation: Conversation = None

    # Task-scoped workspace
    workspace: Workspace = None

    # Runtime-only execution state
    execution: Execution | None = None

    # Security
    security_assessment: str | None = None

    # State metadata
    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)

    @classmethod
    async def start_task(
        cls, query: str, user_id: str = "default", conversation_id: str = None
    ) -> State:
        """Create new task with fresh workspace."""
        from ..storage.state import SQLite

        # Load user profile
        from . import Conversation, Execution, Profile, Workspace

        store = SQLite()
        state_key = f"{user_id}:default"
        profile = await store.load_user_profile(state_key)
        if profile is None:
            profile = Profile(user_id=user_id)

        # Load or create conversation
        if conversation_id:
            conversation = await store.load_conversation(conversation_id, user_id)
            if conversation is None:
                raise ValueError(f"No conversation found for conversation_id: {conversation_id}")
        else:
            conversation = Conversation(user_id=user_id)
            await store.save_conversation(conversation)

        # Create fresh workspace for this task
        workspace = Workspace(objective=query)

        # Create runtime execution state
        execution = Execution()

        # Load conversation history into execution for context
        execution.messages = conversation.messages.copy()

        state = cls(
            query=query,
            user_id=user_id,
            profile=profile,
            conversation=conversation,
            workspace=workspace,
            execution=execution,
        )

        # Save new workspace
        await store.save_task_workspace(state.task_id, state.user_id, state.workspace)

        return state

    @classmethod
    async def continue_task(cls, task_id: str, user_id: str = "default") -> State:
        """Resume existing task with preserved workspace."""
        from ..storage.state import SQLite
        from . import Conversation, Execution

        store = SQLite()

        # Load user profile
        state_key = f"{user_id}:default"
        profile = await store.load_user_profile(state_key)
        if profile is None:
            raise ValueError(f"No user profile found for user_id: {user_id}")

        # Load existing task workspace
        workspace_data = await store.load_task_workspace(task_id, user_id)
        if workspace_data is None:
            raise ValueError(f"No workspace found for task_id: {task_id}")

        # TODO: Need to link conversation_id to workspace to load proper conversation
        # For now, create empty conversation - this needs conversation_id in workspace
        conversation = Conversation(user_id=user_id)

        # Create fresh runtime execution state
        execution = Execution()

        return cls(
            query=workspace_data.objective,  # Extract original query from workspace
            user_id=user_id,
            task_id=task_id,
            profile=profile,
            conversation=conversation,
            workspace=workspace_data,
            execution=execution,
        )

    async def complete_task(self) -> None:
        """Finalize task and cleanup workspace."""
        from ..storage.state import SQLite

        store = SQLite()

        # Save final profile updates
        state_key = f"{self.user_id}:default"
        await store.save_user_profile(state_key, self.profile)

        # Save final conversation updates
        await store.save_conversation(self.conversation)

        # Delete workspace - task finished
        await store.delete_task_workspace(self.task_id)

        # Execution state discarded automatically

    def __post_init__(self):
        """Initialize components for direct construction fallback."""
        from . import Conversation, Execution, Profile, Workspace

        if self.profile is None:
            self.profile = Profile(user_id=self.user_id)

        if self.conversation is None:
            self.conversation = Conversation(user_id=self.user_id)

        if self.workspace is None:
            self.workspace = Workspace(objective=self.query)
        elif not self.workspace.objective:
            self.workspace.objective = self.query

        if self.execution is None:
            self.execution = Execution()

    def update_from_reasoning(self, reasoning_data: Dict[str, Any]) -> None:
        """Update state from LLM reasoning response - delegates to mutations."""
        from .mutations import update_from_reasoning

        update_from_reasoning(self, reasoning_data)

    def get_situated_context(self) -> str:
        """Get user context for prompt injection - delegates to mutations."""
        from .mutations import get_situated_context

        return get_situated_context(self)
