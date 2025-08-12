"""Storage protocol for foundational persistence infrastructure."""

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from cogency.knowledge import KnowledgeArtifact
    from cogency.memory import Profile
    from cogency.state import Conversation, Workspace


@runtime_checkable
class Store(Protocol):
    """Store interface for agent state persistence."""

    # Profile Operations (permanent user identity)

    async def save_profile(self, state_key: str, profile: "Profile") -> bool:
        """Save user profile to storage"""
        ...

    async def load_profile(self, state_key: str) -> "Profile | None":
        """Load user profile from storage"""
        ...

    async def delete_profile(self, state_key: str) -> bool:
        """Delete user profile permanently"""
        ...

    # Conversation Operations (persistent message history)

    async def save_conversation(self, conversation: "Conversation") -> bool:
        """Save conversation to storage"""
        ...

    async def load_conversation(self, conversation_id: str, user_id: str) -> "Conversation | None":
        """Load conversation from storage"""
        ...

    async def delete_conversation(self, conversation_id: str) -> bool:
        """Delete conversation permanently"""
        ...

    # Workspace Operations (temporary execution state)

    async def save_workspace(self, workspace: "Workspace") -> bool:
        """Save workspace to storage"""
        ...

    async def load_workspace(self, conversation_id: str, user_id: str) -> "Workspace | None":
        """Load workspace from storage"""
        ...

    async def delete_workspace(self, conversation_id: str) -> bool:
        """Delete workspace"""
        ...

    # Knowledge Operations (structured knowledge artifacts)

    async def save_knowledge(self, artifact: "KnowledgeArtifact") -> bool:
        """Save knowledge artifact with hybrid storage (embeddings + structure)"""
        ...

    async def search_knowledge(
        self, query: str, user_id: str = "default", top_k: int = 5, threshold: float = 0.7
    ) -> list["KnowledgeArtifact"]:
        """Search knowledge artifacts using semantic similarity"""
        ...

    async def load_knowledge(self, topic: str, user_id: str) -> "KnowledgeArtifact | None":
        """Load specific knowledge artifact by topic"""
        ...

    async def delete_knowledge(self, topic: str, user_id: str) -> bool:
        """Delete knowledge artifact"""
        ...
