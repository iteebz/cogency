"""Anthropic provider - LLM protocol implementation.

HTTP-only provider. WebSocket sessions not supported by Anthropic API.
"""
# pyright: reportAttributeAccessIssue=false, reportCallIssue=false
# Anthropic SDK type stubs are incomplete - runtime behavior is correct

from collections.abc import AsyncGenerator
from typing import Any, cast

from cogency.core.protocols import LLM

from .interrupt import interruptible
from .rotation import with_rotation


class Anthropic(LLM):
    """Anthropic provider implementing HTTP-only LLM protocol."""

    def __init__(
        self,
        api_key: str | None = None,
        http_model: str = "claude-3-5-sonnet-20241022",
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ):
        from .rotation import get_api_key

        self.api_key = api_key or get_api_key("anthropic")
        if not self.api_key:
            raise ValueError("No Anthropic API key found")
        self.http_model = http_model
        self.temperature = temperature
        self.max_tokens = max_tokens

    def _create_client(self, api_key: str):
        import anthropic

        return anthropic.AsyncAnthropic(api_key=api_key)

    def _format_messages(self, messages: list[dict[str, Any]]) -> tuple[str, list[dict[str, Any]]]:
        system_parts: list[str] = []
        conversation: list[dict[str, Any]] = []

        for msg in messages:
            if msg["role"] == "system":
                system_parts.append(msg["content"])
            else:
                conversation.append(msg)

        return "\n".join(system_parts), conversation

    async def generate(self, messages: list[dict[str, Any]]) -> str:
        async def _generate_with_key(api_key: str) -> str:
            try:
                client = self._create_client(api_key)
                system, conversation = self._format_messages(messages)
                response = await client.messages.create(
                    model=self.http_model,
                    system=system,
                    messages=cast("Any", conversation),
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                )
                first_block = response.content[0]
                if hasattr(first_block, "text"):
                    return cast("Any", first_block).text
                return ""
            except ImportError as e:
                raise ImportError("Please install anthropic: pip install anthropic") from e

        return await with_rotation("ANTHROPIC", _generate_with_key)

    @interruptible
    async def stream(self, messages: list[dict[str, Any]]) -> AsyncGenerator[str, None]:
        async def _stream_with_key(api_key: str):
            client = self._create_client(api_key)
            system, conversation = self._format_messages(messages)
            return client.messages.stream(
                model=self.http_model,
                system=system,
                messages=cast("Any", conversation),
                max_tokens=self.max_tokens,
                temperature=self.temperature,
            )

        # Get streaming context manager with rotation
        stream_context_manager = await with_rotation("ANTHROPIC", _stream_with_key)

        # Enter the context manager to get the stream object
        async with stream_context_manager as stream_object:
            async for text in stream_object.text_stream:
                yield text

    async def connect(self, messages: list[dict[str, Any]]) -> "LLM":
        raise NotImplementedError("Anthropic does not support WebSocket sessions")

    async def send(self, content: str) -> AsyncGenerator[str, None]:
        raise NotImplementedError("Anthropic does not support WebSocket sessions")
        yield  # unreachable, makes this an async generator

    async def close(self) -> None:
        pass
