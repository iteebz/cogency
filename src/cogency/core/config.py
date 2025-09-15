"""Agent execution configuration."""

from dataclasses import dataclass

from .protocols import LLM, Storage, Tool


@dataclass(frozen=True)
class Config:
    """Immutable agent configuration.

    Frozen dataclass ensures configuration cannot be modified after creation.
    Runtime parameters (query, user_id, conversation_id) are passed per call.
    """

    # Capabilities
    llm: LLM
    storage: Storage
    tools: list[Tool]

    # User steering layer
    instructions: str | None = None

    # Execution behavior
    max_iterations: int = 10  # [SEC-005] Prevent runaway agents
    mode: str = "auto"
    profile: bool = True
    sandbox: bool = True
    learning_cadence: int = 5
    history_window: int = 20  # Max conversation history messages to include
