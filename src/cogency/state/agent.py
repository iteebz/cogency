"""Split-State Model - Semantic boundaries with targeted persistence."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class UserProfile:
    """Persistent user context across sessions."""

    user_id: str
    preferences: Dict[str, Any] = field(default_factory=dict)
    goals: List[str] = field(default_factory=list)
    expertise_areas: List[str] = field(default_factory=list)
    communication_style: str = ""
    projects: Dict[str, str] = field(default_factory=dict)
    interaction_count: int = 0  # LEGACY: For memory tests

    created_at: datetime = field(default=None)
    last_updated: datetime = field(default=None)

    def __post_init__(self):
        """Ensure both timestamps are set to same value on creation."""
        if self.created_at is None or self.last_updated is None:
            now = datetime.now()
            if self.created_at is None:
                self.created_at = now
            if self.last_updated is None:
                self.last_updated = now


@dataclass
class Workspace:
    """Ephemeral task state within sessions."""

    objective: str = ""
    assessment: str = ""
    approach: str = ""
    observations: List[str] = field(default_factory=list)
    insights: List[str] = field(default_factory=list)
    facts: Dict[str, Any] = field(default_factory=dict)
    thoughts: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class ExecutionState:
    """Runtime-only execution mechanics - NOT persisted."""

    iteration: int = 0
    max_iterations: int = 10
    mode: str = "adapt"
    stop_reason: Optional[str] = None

    messages: List[Dict[str, Any]] = field(default_factory=list)
    response: Optional[str] = None

    pending_calls: List[Dict[str, Any]] = field(default_factory=list)
    completed_calls: List[Dict[str, Any]] = field(default_factory=list)
    iterations_without_tools: int = 0
    tool_results: Dict[str, Any] = field(default_factory=dict)


@dataclass
class State:
    """Canonical Three-Horizon Split-State Model - matches docs/dev/state.md exactly"""

    # Identity
    query: str
    user_id: str = "default"
    task_id: str = field(default_factory=lambda: str(__import__("uuid").uuid4()))

    # Horizon 1: Permanent Memory (persisted in user_profiles table)
    profile: UserProfile = None

    # Horizon 2: Task-Scoped Workspace (persisted in task_workspaces table by task_id)
    workspace: Workspace = None

    # Horizon 3: Runtime Execution (NEVER persisted - runtime-only)
    execution: Optional[ExecutionState] = None

    # Security
    security_assessment: Optional[str] = None

    # State metadata
    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)

    @classmethod
    async def start_task(cls, query: str, user_id: str = "default") -> "State":
        """CANONICAL: Create new task with fresh workspace - Horizon 2 created"""
        from ..storage.state import Persistence

        # Load Horizon 1: UserProfile from user_profiles table
        persistence = Persistence()
        profile = await persistence.load_user_profile(user_id)
        if profile is None:
            profile = UserProfile(user_id=user_id)

        # Create fresh Horizon 2: Workspace for this specific task
        workspace = Workspace(objective=query)

        # Create fresh Horizon 3: ExecutionState (runtime-only, never persisted)
        execution = ExecutionState()

        state = cls(
            query=query, user_id=user_id, profile=profile, workspace=workspace, execution=execution
        )

        # Save new workspace to task_workspaces table by task_id
        await persistence.save_task_workspace(state.task_id, state.user_id, state.workspace)

        return state

    @classmethod
    async def continue_task(cls, task_id: str, user_id: str = "default") -> "State":
        """CANONICAL: Resume existing task with preserved workspace - Horizon 2 loaded"""
        from ..storage.state import Persistence

        persistence = Persistence()

        # Load Horizon 1: UserProfile from user_profiles table
        profile = await persistence.load_user_profile(user_id)
        if profile is None:
            raise ValueError(f"No user profile found for user_id: {user_id}")

        # Load Horizon 2: Existing workspace from task_workspaces table
        workspace_data = await persistence.load_task_workspace(task_id, user_id)
        if workspace_data is None:
            raise ValueError(f"No workspace found for task_id: {task_id}")

        # Create fresh Horizon 3: ExecutionState (always runtime-only)
        execution = ExecutionState()

        return cls(
            query=workspace_data.get("objective", ""),  # Extract original query
            user_id=user_id,
            task_id=task_id,
            profile=profile,
            workspace=workspace_data,
            execution=execution,
        )

    async def complete_task(self) -> None:
        """CANONICAL: Finalize task and cleanup workspace - Horizon 2 deleted"""
        from ..storage.state import Persistence

        persistence = Persistence()

        # Save final Horizon 1: UserProfile updates to user_profiles table
        await persistence.save_user_profile(self.user_id, self.profile)

        # DELETE Horizon 2: Workspace from task_workspaces table - task finished
        await persistence.delete_task_workspace(self.task_id)

        # Horizon 3: ExecutionState discarded automatically (never persisted)

    def __post_init__(self):
        """Initialize components for direct construction - CANONICAL fallback only."""
        if self.profile is None:
            self.profile = UserProfile(user_id=self.user_id)

        if self.workspace is None:
            self.workspace = Workspace(objective=self.query)
        elif not self.workspace.objective:
            self.workspace.objective = self.query

        if self.execution is None:
            self.execution = ExecutionState()

    def update_from_reasoning(self, reasoning_data: Dict[str, Any]) -> None:
        """Update state from LLM reasoning response - delegates to mutations."""
        from .mutations import update_from_reasoning

        update_from_reasoning(self, reasoning_data)

    def get_situated_context(self) -> str:
        """Get user context for prompt injection - delegates to mutations."""
        from .mutations import get_situated_context

        return get_situated_context(self)
