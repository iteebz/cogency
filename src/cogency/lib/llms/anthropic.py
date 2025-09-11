"""Anthropic provider - LLM protocol implementation.

Note: WebSocket streaming not yet supported by Anthropic API (as of August 2025).
Uses HTTP with Server-Sent s fallback. Streaming architecture ready
for WebSocket when Anthropic adds support.
"""

from collections.abc import AsyncGenerator

from ...core.protocols import LLM
from ...core.result import Err, Ok, Result
from ..rotation import rotate
from .interrupt import interruptible


class Anthropic(LLM):
    """Anthropic provider implementing LLM protocol."""

    def __init__(
        self,
        api_key: str = None,
        llm_model: str = "claude-3-5-sonnet-20241022",
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ):
        from ..credentials import detect_api_key

        self.api_key = api_key or detect_api_key("anthropic")
        self.llm_model = llm_model
        self.temperature = temperature
        self.max_tokens = max_tokens

    def _create_client(self, api_key: str):
        """Create Anthropic client for given API key."""
        import anthropic

        return anthropic.AsyncAnthropic(api_key=api_key)

    @rotate
    async def generate(self, client, messages: list[dict]) -> Result[str]:
        """Generate complete response from conversation messages."""
        try:
            response = await client.messages.create(
                model=self.llm_model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
            )

            return Ok(response.content[0].text)

        except ImportError:
            return Err("Please install anthropic: pip install anthropic")
        except Exception as e:
            return Err(f"Anthropic Generate Error: {str(e)}")

    @rotate
    async def connect(self, client, messages: list[dict]) -> Result[object]:
        """INFRASTRUCTURE: Create streaming connection with error handling."""
        try:
            # Create stream connection (pre-configured, ready to use)
            stream_connection = client.messages.stream(
                model=self.llm_model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
            )

            return Ok(stream_connection)

        except ImportError:
            return Err("Please install anthropic: pip install anthropic")
        except Exception as e:
            return Err(f"Anthropic Connection Error: {str(e)}")

    @rotate
    @interruptible
    async def stream(self, client, messages: list[dict]) -> AsyncGenerator[str, None]:
        """Generate streaming tokens from conversation messages."""
        try:
            async with client.messages.stream(
                model=self.llm_model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
            ) as stream:
                async for text in stream.text_stream:
                    yield text
        except Exception as e:
            raise RuntimeError(f"Anthropic streaming error: {str(e)}") from e
