"""Core protocols for provider abstraction."""

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
