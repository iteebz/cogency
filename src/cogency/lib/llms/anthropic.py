"""Anthropic provider - LLM protocol implementation.

HTTP-only provider. WebSocket sessions not supported by Anthropic API.
"""

from collections.abc import AsyncGenerator

from ...core.protocols import LLM
from ..rotation import with_rotation
from .interrupt import interruptible


class Anthropic(LLM):
    """Anthropic provider implementing HTTP-only LLM protocol."""

    def __init__(
        self,
        api_key: str = None,
        http_model: str = "claude-3-5-sonnet-20241022",
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ):
        from ..rotation import get_api_key

        self.api_key = api_key or get_api_key("anthropic")
        if not self.api_key:
            raise RuntimeError("No Anthropic API key found")
        self.http_model = http_model
        self.temperature = temperature
        self.max_tokens = max_tokens

    def _create_client(self, api_key: str):
        """Create Anthropic client for given API key."""
        import anthropic

        return anthropic.AsyncAnthropic(api_key=api_key)

    async def generate(self, messages: list[dict]) -> str:
        """Generate complete response from conversation messages."""

        async def _generate_with_key(api_key: str) -> str:
            try:
                client = self._create_client(api_key)
                response = await client.messages.create(
                    model=self.http_model,
                    messages=messages,
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                )
                return response.content[0].text
            except ImportError as e:
                raise ImportError("Please install anthropic: pip install anthropic") from e
            except Exception as e:
                raise RuntimeError(f"Anthropic generate error: {str(e)}") from e

        return await with_rotation("ANTHROPIC", _generate_with_key)

    @interruptible
    async def stream(self, messages: list[dict]) -> AsyncGenerator[str, None]:
        """Generate streaming tokens from conversation messages."""

        async def _stream_with_key(api_key: str):
            client = self._create_client(api_key)
            return client.messages.stream(
                model=self.http_model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
            )

        # Get streaming context manager with rotation
        stream_ctx = await with_rotation("ANTHROPIC", _stream_with_key)

        try:
            async with stream_ctx as stream:
                async for text in stream.text_stream:
                    yield text
        except Exception as e:
            raise RuntimeError(f"Anthropic streaming error: {str(e)}") from e

    # WebSocket methods - not supported by Anthropic
    async def connect(self, messages: list[dict]) -> "LLM":
        """WebSocket sessions not supported by Anthropic API."""
        raise NotImplementedError("Anthropic does not support WebSocket sessions")

    async def send(self, content: str) -> AsyncGenerator[str, None]:
        """WebSocket sessions not supported by Anthropic API."""
        raise NotImplementedError("Anthropic does not support WebSocket sessions")

    async def close(self) -> None:
        """No-op for HTTP-only provider."""
        pass
