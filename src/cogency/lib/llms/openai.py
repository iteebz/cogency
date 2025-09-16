"""OpenAI provider implementing LLM protocol with WebSocket support."""

from collections.abc import AsyncGenerator

from ...core.protocols import LLM
from ..logger import logger
from ..rotation import get_api_key, with_rotation
from .interrupt import interruptible


class OpenAI(LLM):
    """OpenAI provider with HTTP streaming and WebSocket (Realtime API) support."""

    def __init__(
        self,
        api_key: str = None,
        http_model: str = "gpt-4o-mini",
        websocket_model: str = "gpt-4o-mini-realtime-preview",
        temperature: float = 1.0,
        max_tokens: int = 2000,
    ):
        self.api_key = api_key or get_api_key("openai")
        if not self.api_key:
            raise RuntimeError("No API key found")
        self.http_model = http_model
        self.websocket_model = websocket_model
        self.temperature = temperature
        self.max_tokens = max_tokens

        # WebSocket session state
        self._connection = None
        self._connection_manager = None

    def _create_client(self, api_key: str):
        """Create OpenAI client for given API key."""
        import openai

        return openai.AsyncOpenAI(api_key=api_key)

    async def generate(self, messages: list[dict]) -> str:
        """One-shot completion with full conversation context."""

        async def _generate_with_key(api_key: str) -> str:
            try:
                client = self._create_client(api_key)
                response = await client.chat.completions.create(
                    model=self.http_model,
                    messages=messages,
                    max_completion_tokens=self.max_tokens,
                    temperature=self.temperature,
                    stream=False,
                )
                return response.choices[0].message.content
            except ImportError as e:
                raise ImportError("Please install openai: pip install openai") from e
            except Exception as e:
                raise RuntimeError(f"OpenAI Generate Error: {str(e)}") from e

        return await with_rotation("OPENAI", _generate_with_key)

    @interruptible
    async def stream(self, messages: list[dict]) -> AsyncGenerator[str, None]:
        """HTTP streaming with full conversation context."""

        async def _stream_with_key(api_key: str):
            client = self._create_client(api_key)
            return await client.chat.completions.create(
                model=self.http_model,
                messages=messages,
                max_completion_tokens=self.max_tokens,
                temperature=self.temperature,
                stream=True,
            )

        response = await with_rotation("OPENAI", _stream_with_key)

        # Stream native chunks without modification
        async for chunk in response:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    async def connect(self, messages: list[dict]) -> "OpenAI":
        """Create session with initial context. Returns session-enabled OpenAI instance."""

        # Close any existing session first
        if self._connection_manager:
            await self.close()

        try:
            # Get fresh API key for WebSocket session
            async def _create_client_with_key(api_key: str):
                return self._create_client(api_key)

            client = await with_rotation("OPENAI", _create_client_with_key)
            connection_manager = client.beta.realtime.connect(model=self.websocket_model)
            connection = await connection_manager.__aenter__()

            # Configure for text responses with proper system instructions
            system_content = ""
            user_messages = []

            for msg in messages:
                if msg["role"] == "system":
                    system_content += msg["content"] + "\n"
                else:
                    user_messages.append(msg)

            await connection.session.update(
                session={
                    "modalities": ["text"],
                    "temperature": self.temperature,
                    "max_response_output_tokens": 2000,
                    "instructions": system_content.strip(),
                }
            )

            # Send each user message properly and trigger response generation
            for msg in user_messages:
                await connection.conversation.item.create(
                    item={
                        "type": "message",
                        "role": msg["role"],
                        "content": [{"type": "input_text", "text": msg["content"]}],
                    }
                )

            # Note: send() will trigger response generation when first message is sent

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
            logger.warning(f"OpenAI WebSocket connection failed: {e}")
            raise RuntimeError(f"OpenAI connection failed: {e}") from e

    async def send(self, content: str) -> AsyncGenerator[str, None]:
        """Send message in session and stream response until turn completion."""
        if not self._connection:
            raise RuntimeError("send() requires active session. Call connect() first.")

        try:
            # Only add message if content is provided (avoid double-send after connect)
            if content.strip():
                await self._connection.conversation.item.create(
                    item={
                        "type": "message",
                        "role": "user",
                        "content": [{"type": "input_text", "text": content}],
                    }
                )

            # Try to create response, but handle active response gracefully
            try:
                await self._connection.response.create()
            except Exception as e:
                if "already has an active response" in str(e):
                    # Continue with existing response stream
                    pass
                else:
                    raise

            # Stream response chunks until turn completion
            async for event in self._connection:
                if event.type == "response.text.delta" and event.delta:
                    yield event.delta
                elif event.type == "response.done":
                    return
                elif event.type == "error":
                    if "already has an active response" in str(event):
                        # Ignore this error and continue
                        continue
                    logger.warning(f"OpenAI session error: {event}")
                    return

        except Exception as e:
            logger.warning(f"OpenAI session send failed: {e}")
            return

    async def close(self) -> None:
        """Close session and cleanup resources."""
        if not self._connection_manager:
            return  # No-op for HTTP-only instances

        try:
            import asyncio

            # Force close connection first
            if self._connection:
                import contextlib

                with contextlib.suppress(Exception):
                    await self._connection.close()

            await asyncio.wait_for(
                self._connection_manager.__aexit__(None, None, None), timeout=5.0
            )
            self._connection = None
            self._connection_manager = None
        except Exception as e:
            logger.warning(f"OpenAI session close failed: {e}")
            # Force cleanup even if close fails
            self._connection = None
            self._connection_manager = None
