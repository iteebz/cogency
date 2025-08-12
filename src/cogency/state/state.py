"""State class with lifecycle management."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Any
from uuid import uuid4

from cogency.knowledge.extract import extract
from cogency.memory import learn
from cogency.storage.sqlite import SQLite

if TYPE_CHECKING:
    from . import Conversation, Execution, Workspace


@dataclass
class State:
    """Pure ephemeral execution state."""

    # Identity
    query: str
    user_id: str = "default"
    task_id: str = field(default_factory=lambda: str(uuid4()))

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
        from . import Conversation, Execution, Workspace

        store = SQLite()

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
            conversation=conversation,
            workspace=workspace,
            execution=execution,
        )

        # Save new workspace
        await store.save_workspace(state.task_id, state.user_id, state.workspace)

        return state

    async def extract_knowledge(self, memory=None) -> None:
        """Extract knowledge from conversation - canonical domain operation."""
        await extract(self, memory)

    async def learn_profile(self, memory=None) -> None:
        """Learn user profile patterns - canonical domain operation."""
        await learn(self, memory)

    @classmethod
    async def continue_task(cls, task_id: str, user_id: str = "default") -> State:
        """Resume existing task with preserved workspace."""
        from . import Conversation, Execution

        store = SQLite()

        # Load existing task workspace
        workspace_data = await store.load_workspace(task_id, user_id)
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
            conversation=conversation,
            workspace=workspace_data,
            execution=execution,
        )

    # Archive functionality removed - knowledge extraction now handled by knowledge domain directly

    def __post_init__(self):
        """Initialize components for direct construction fallback."""
        from . import Conversation, Execution, Workspace

        if self.conversation is None:
            self.conversation = Conversation(user_id=self.user_id)

        if self.workspace is None:
            self.workspace = Workspace(objective=self.query)
        elif not self.workspace.objective:
            self.workspace.objective = self.query

        if self.execution is None:
            self.execution = Execution()

    def update_from_reasoning(self, reasoning_data: dict[str, Any]) -> None:
        """Update state from LLM reasoning response."""
        # TODO: Implement direct state updates if needed
        # For now, state updates happen through normal attribute access
        pass

    def context(self) -> str:
        """Build system context from workspace, execution - NO conversation or profile."""
        parts = []

        # Workspace context
        if self.workspace:
            if self.workspace.objective:
                parts.append(f"Current objective: {self.workspace.objective}")
            if self.workspace.insights:
                parts.append(f"Key insights: {'; '.join(self.workspace.insights[-2:])}")

        # Tool execution history - canonical feedback format
        if self.execution and hasattr(self.execution, "completed_calls"):
            parts.append("TOOL EXECUTION HISTORY:")
            for call in self.execution.completed_calls[-3:]:  # Last 3 results
                tool_name = call.get("tool", "unknown")
                success = call.get("success", False)
                result = call.get("result", {})

                # Extract meaningful result summary
                if isinstance(result, dict):
                    if result.get("result"):
                        summary = result["result"]  # e.g., "Created file: hello.py"
                    elif result.get("message"):
                        summary = result["message"]
                    else:
                        summary = "completed"
                else:
                    summary = str(result)

                status = "✅ SUCCESS" if success else "❌ FAILED"
                parts.append(f"- {tool_name}: {status} - {summary}")

        return "\n".join(parts) if parts else ""

    def messages(self) -> list[dict]:
        """Get conversation messages for LLM chat interface."""
        if self.conversation and self.conversation.messages:
            return self.conversation.messages.copy()
        return []


# Agent state management - Database-as-State architecture.
# Pure data + pure functions = beautiful state management.


@dataclass
class Workspace:
    """Ephemeral task state within sessions."""

    objective: str = ""
    assessment: str = ""
    approach: str = ""
    observations: list[str] = field(default_factory=list)
    insights: list[str] = field(default_factory=list)
    facts: dict[str, Any] = field(default_factory=dict)
    thoughts: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class Conversation:
    """Persistent conversation history across tasks."""

    conversation_id: str = field(default_factory=lambda: str(uuid4()))
    user_id: str = ""
    messages: list[dict[str, Any]] = field(default_factory=list)
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class Execution:
    """Runtime-only execution mechanics - NOT persisted."""

    iteration: int = 0
    max_iterations: int = 10
    stop_reason: str | None = None

    messages: list[dict[str, Any]] = field(default_factory=list)
    response: str | None = None

    pending_calls: list[dict[str, Any]] = field(default_factory=list)
    completed_calls: list[dict[str, Any]] = field(default_factory=list)
    iterations_without_tools: int = 0
    tool_results: dict[str, Any] = field(default_factory=dict)


__all__ = ["Workspace", "Conversation", "Execution", "State"]
