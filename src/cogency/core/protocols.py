"""Core protocols for provider abstraction."""

from abc import ABC, abstractmethod
from typing import Protocol, runtime_checkable

from ..lib.result import Result


@runtime_checkable
class LLM(Protocol):
    """Text generation protocol."""

    async def generate(self, messages: list[dict]) -> Result[str, str]:
        """Generate text from conversation messages.

        Args:
            messages: List of {"role": str, "content": str} dicts

        Returns:
            Ok(generated_text) on success
            Err(error_message) on failure
        """
        ...


@runtime_checkable
class Embedder(Protocol):
    """Vector embedding protocol."""

    async def embed(self, texts: list[str]) -> Result[list[list[float]], str]:
        """Generate embeddings for input texts.

        Args:
            texts: List of strings to embed

        Returns:
            Ok(list of embedding vectors) on success
            Err(error_message) on failure
        """
        ...


class Tool(ABC):
    """Tool interface with agent assistance capabilities."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Tool name for agent reference."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Tool description for agent understanding."""
        pass

    @property
    def schema(self) -> dict:
        """Parameter schema for accurate agent tool calls."""
        return {}

    @property
    def examples(self) -> list[dict]:
        """Usage examples for agent learning."""
        return []

    @abstractmethod
    async def execute(self, **kwargs) -> Result[str, str]:
        """Execute tool with given arguments."""
        pass
