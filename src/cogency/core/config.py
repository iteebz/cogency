from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

from .protocols import LLM, HistoryTransform, NotificationSource, Storage, Tool

# Security access levels for file and shell operations
Access = Literal["sandbox", "project", "system"]


@dataclass(frozen=True)
class Execution:
    """Execution dependencies exposed as an immutable value object."""

    storage: Storage
    tools: Sequence[Tool]
    shell_timeout: int
    sandbox_dir: str
    access: Access


@dataclass(frozen=True)
class Security:
    """Security policies for agent execution."""

    access: Access = "sandbox"
    sandbox_dir: str = ".cogency/sandbox"  # Sandbox directory (ignored unless access="sandbox")
    shell_timeout: int = 30  # Shell command timeout in seconds
    api_timeout: float = 30.0  # HTTP/LLM call timeout


@dataclass(frozen=True)
class Config:
    """Immutable agent configuration.

    Frozen dataclass ensures configuration cannot be modified after creation.
    Runtime parameters (query, user_id, conversation_id) are passed per call.

    Immutability guarantees thread-safety for shared agent instances.
    """

    # Core capabilities
    llm: LLM
    storage: Storage
    tools: list[Tool]

    # Policies
    security: Security = Security()

    # Execution behavior
    identity: str | None = None  # Core agent identity
    instructions: str | None = None  # User steering
    mode: str = "auto"  # Execution mode
    max_iterations: int = 10  # Execution bounds
    history_window: int | None = None  # Context scope (None = full history)
    history_transform: HistoryTransform | None = None  # Optional history compression
    profile: bool = False  # Learning enabled
    profile_cadence: int = 5  # Messages between profile learning
    debug: bool = False  # Debug logging to .cogency/debug/
    notifications: NotificationSource | None = None

    @property
    def execution(self) -> Execution:
        """Return cohesive execution dependencies for downstream consumers."""

        return Execution(
            storage=self.storage,
            tools=tuple(self.tools),
            shell_timeout=self.security.shell_timeout,
            sandbox_dir=self.security.sandbox_dir,
            access=self.security.access,
        )
