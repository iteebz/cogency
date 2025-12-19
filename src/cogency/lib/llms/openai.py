# pyright: reportAttributeAccessIssue=false
# pyright: reportUnknownMemberType=false
# OpenAI SDK type stubs are incomplete - runtime behavior is correct

import logging
from collections.abc import AsyncGenerator
from typing import Any, cast

from cogency.core.protocols import LLM

from .interrupt import interruptible
from .rotation import get_api_key, with_rotation

logger = logging.getLogger(__name__)

# WebSocket connection cleanup timeout. Based on:
# - Typical close handshake: 100-500ms
# - Network latency buffer: 1-2s
# - Stuck connections (server unresponsive): force close after 5s
# Prevents indefinite hangs during cleanup while allowing graceful shutdown
WS_CLOSE_TIMEOUT_SECONDS = 5.0


class OpenAI(LLM):
    """OpenAI provider with HTTP streaming and WebSocket (Realtime API) support."""

    def __init__(
        self,
        api_key: str | None = None,
        http_model: str = "gpt-5.2",
        websocket_model: str = "gpt-realtime",
        temperature: float = 1.0,
        max_tokens: int = 4096,
    ):
        self.api_key = api_key or get_api_key("openai")
        if not self.api_key:
            raise ValueError("No API key found")
        self.http_model = http_model
        self.websocket_model = websocket_model
        self.temperature = temperature
        self.max_tokens = max_tokens

        # WebSocket session state (SDK types)
        self._connection: Any = None  # openai.AsyncSession - incomplete stubs
        self._connection_manager: Any = None  # AsyncContextManager - runtime protocol

    def _create_client(self, api_key: str):
        import openai

        return openai.AsyncOpenAI(api_key=api_key)

    async def generate(self, messages: list[dict[str, Any]]) -> str:
        async def _generate_with_key(api_key: str) -> str:
            try:
                client = self._create_client(api_key)

                final_instructions, final_input_messages = self._format_messages(messages)

                response = await client.responses.create(
                    model=self.http_model,
                    instructions=final_instructions,
                    input=cast("Any", final_input_messages),  # SDK expects strict type
                    temperature=self.temperature,
                    stream=False,
                )
                if response.output_text:
                    return response.output_text
                if response.output and len(response.output) > 0:
                    output_msg: Any = response.output[0]  # SDK dynamic response type
                    if output_msg.content and len(output_msg.content) > 0:
                        return str(output_msg.content[0].text or "")
                return ""
            except ImportError as e:
                raise ImportError("Please install openai: pip install openai") from e

        return await with_rotation("OPENAI", _generate_with_key)

    @interruptible
    async def stream(self, messages: list[dict[str, Any]]) -> AsyncGenerator[str, None]:
        async def _stream_with_key(api_key: str):
            client = self._create_client(api_key)

            final_instructions, final_input_messages = self._format_messages(messages)

            return await client.responses.create(
                model=self.http_model,
                instructions=final_instructions,
                input=cast("Any", final_input_messages),
                temperature=self.temperature,
                stream=True,
            )

        response_stream = await with_rotation("OPENAI", _stream_with_key)

        async for event in response_stream:
            # Check event type - handles both real ResponseTextDeltaEvent and mocks
            if (
                hasattr(event, "type")
                and event.type == "response.output_text.delta"
                and hasattr(event, "delta")
            ):
                yield event.delta
            elif hasattr(event, "delta") and not hasattr(event, "type"):
                # Fallback for direct delta attribute (legacy format)
                yield event.delta

    async def connect(self, messages: list[dict[str, Any]]) -> "OpenAI":
        # Close any existing session first
        if self._connection_manager:
            await self.close()

        # Get fresh API key for WebSocket session
        async def _create_client_with_key(api_key: str):
            return self._create_client(api_key)

        try:
            client = await with_rotation("OPENAI", _create_client_with_key)
            connection_manager = client.realtime.connect(model=self.websocket_model)
            connection = await connection_manager.__aenter__()

            # Configure for text responses with proper system instructions
            system_content = ""
            user_messages = []

            for msg in messages:
                if msg["role"] == "system":
                    system_content += msg["content"] + "\n"
                else:
                    user_messages.append(msg)

            logger.debug(
                f"OpenAI session instructions ({len(system_content)} chars): {system_content[:200]}..."
            )
            await connection.session.update(
                session={
                    "type": "realtime",
                    "instructions": system_content.strip(),
                    "output_modalities": ["text"],
                }
            )

            # Add ALL history messages including last user message
            # WebSocket needs full conversation loaded before response.create()
            for msg in cast("list[dict[str, Any]]", user_messages):
                # Assistant messages use "output_text" type, user messages use "input_text"
                content_type = "output_text" if msg["role"] == "assistant" else "input_text"
                await connection.conversation.item.create(
                    item=cast("Any", {
                        "type": "message",
                        "role": msg["role"],
                        "content": [{"type": content_type, "text": msg["content"]}],
                    })
                )

            # Create session-enabled instance with fresh key
            fresh_key = client.api_key
            session_instance = OpenAI(
                api_key=fresh_key,
                http_model=self.http_model,
                websocket_model=self.websocket_model,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )
            session_instance._connection = connection
            session_instance._connection_manager = connection_manager

            return session_instance
        except Exception as e:
            logger.warning(f"OpenAI connection failed: {e}")
            raise RuntimeError("OpenAI connection failed") from e

    @interruptible
    async def send(self, content: str) -> AsyncGenerator[str, None]:  # noqa: C901  # OpenAI protocol adapter with error recovery
        if not self._connection:
            raise RuntimeError("send() requires active session. Call connect() first.")

        try:
            # Add message if content is provided
            if content.strip():
                await self._connection.conversation.item.create(
                    item={
                        "type": "message",
                        "role": "user",
                        "content": [{"type": "input_text", "text": content}],
                    }
                )
        except Exception as e:
            logger.error(f"Error sending message in OpenAI session: {e}")
            raise

        try:
            await self._connection.response.create()
        except Exception as e:
            if hasattr(e, "code") and e.code == "active_response_exists":
                pass
            elif "already has an active response" in str(e).lower():
                logger.debug("Active response detected via string match (fragile)")
            else:
                raise

        # Stream response chunks until turn completion
        chunk_count = 0
        while True:
            try:
                event = await self._connection.recv()
                logger.debug(f"recv() got event: {event.type}")
                if event.type == "response.output_text.delta" and hasattr(event, "delta"):
                    chunk_count += 1
                    logger.debug(f"Yielding delta {chunk_count}: {event.delta[:50]}")
                    yield event.delta
                elif event.type == "response.done":
                    logger.debug(f"Got response.done after {chunk_count} chunks")
                    return
                elif event.type == "response.output_text.done":
                    # Text generation is done, wait for final response.done
                    logger.debug("Got response.output_text.done")
                elif event.type == "error":
                    error_code = getattr(event, "code", None)
                    if error_code == "active_response_exists":
                        continue
                    if "already has an active response" in str(event).lower():
                        logger.debug("Active response error via string match (fragile)")
                        continue
                    logger.warning(f"OpenAI session error: {event}")
                    return
            except Exception as e:
                logger.error(f"Error receiving event: {e}")
                raise

    async def close(self) -> None:
        if not self._connection_manager:
            return  # No-op for HTTP-only instances

        import asyncio

        # Force close connection first
        if self._connection:
            import contextlib

            with contextlib.suppress(Exception):
                await self._connection.close()

        await asyncio.wait_for(
            self._connection_manager.__aexit__(None, None, None), timeout=WS_CLOSE_TIMEOUT_SECONDS
        )
        self._connection = None
        self._connection_manager = None

    def _format_messages(self, messages: list[dict[str, Any]]) -> tuple[str, list[dict[str, str]]]:
        """Converts cogency's message format to OpenAI Responses API's instructions and input format."""
        openai_input_messages: list[dict[str, str]] = []
        system_instructions_parts: list[str] = []

        for msg in messages:
            if msg["role"] == "system":
                system_instructions_parts.append(msg["content"])
            else:
                # OpenAI's Responses API expects 'user' and 'assistant' roles in 'input'.
                # For minimal change, we'll map 'tool' role to 'user' role.
                role: str = msg["role"]
                if role == "tool":
                    role = "user"
                openai_input_messages.append({"role": role, "content": msg["content"]})

        final_instructions = "\n".join(system_instructions_parts).strip()
        return final_instructions, openai_input_messages
