"""Agent execution configuration."""

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

from .protocols import LLM, Storage, Tool

# Security access levels for file and shell operations
Access = Literal["sandbox", "project", "system"]


@dataclass(frozen=True)
class Execution:
    """Execution dependencies exposed as an immutable value object."""

    storage: Storage
    tools: Sequence[Tool]
    shell_timeout: int
    scrape_limit: int


@dataclass(frozen=True)
class Security:
    """Security policies for agent execution."""

    access: Access = "sandbox"
    shell_timeout: int = 30  # Shell command timeout in seconds
    api_timeout: float = 30.0  # HTTP/LLM call timeout


@dataclass(frozen=True)
class Config:
    """Immutable agent configuration.

    Frozen dataclass ensures configuration cannot be modified after creation.
    Runtime parameters (query, user_id, conversation_id) are passed per call.
    """

    # Core capabilities
    llm: LLM
    storage: Storage
    tools: list[Tool]

    # Policies
    security: Security = Security()

    # Execution behavior
    instructions: str | None = None  # User steering
    mode: str = "auto"  # Execution mode
    max_iterations: int = 10  # Execution bounds
    history_window: int = 20  # Context scope
    profile: bool = True  # Learning enabled
    learn_every: int = 5  # Learning frequency

    # Tool configuration
    scrape_limit: int = 3000  # Web content character limit

    @property
    def execution(self) -> Execution:
        """Return cohesive execution dependencies for downstream consumers."""

        return Execution(
            storage=self.storage,
            tools=tuple(self.tools),
            shell_timeout=self.security.shell_timeout,
            scrape_limit=self.scrape_limit,
        )
