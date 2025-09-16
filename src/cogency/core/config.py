"""Agent execution configuration."""

from dataclasses import dataclass

from .protocols import LLM, Storage, Tool


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

    # User personalization
    profile: bool = True
    learning_cadence: int = 5
    history_window: int = 20  # Max conversation history messages to include

    # Execution control
    mode: str = "auto"
    max_iterations: int = 10  # [SEC-005] Prevent runaway agents
    sandbox: bool = True

    # User steering
    instructions: str | None = None
