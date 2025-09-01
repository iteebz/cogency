"""Agent execution configuration."""

from dataclasses import dataclass

from .protocols import LLM, Storage, Tool


@dataclass(frozen=True)
class Config:
    """Immutable agent behavior configuration.

    Config = How the agent works (persistent)
    Runtime params = What the agent does now (per-invocation)
    """

    # Capabilities
    llm: LLM
    storage: Storage
    tools: list[Tool]

    # User steering layer (injection-safe)
    instructions: str | None = None

    # Execution behavior
    max_iterations: int = 3
    mode: str = "auto"
    profile: bool = True
    sandbox: bool = True
