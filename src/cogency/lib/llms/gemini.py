"""Gemini provider implementing LLM protocol with dual-signal completion detection."""

from collections.abc import AsyncGenerator

from ...core.protocols import LLM
from ..logger import logger
from ..rotation import get_api_key, with_rotation
from .interrupt import interruptible


class Gemini(LLM):
    """Gemini provider with HTTP streaming and WebSocket (Live API) support.

    Implements dual-signal completion detection for 100% reliability:
    - generation_complete: Content generation finished
    - turn_complete: Turn interaction finished
    Both signals required to prevent premature stream termination.
    """

    def __init__(
        self,
        api_key: str = None,
        http_model: str = "gemini-2.5-flash",
        websocket_model: str = "gemini-2.5-flash-live-preview",
        temperature: float = 0.7,
    ):
        self.api_key = api_key or get_api_key("gemini")
        if not self.api_key:
            raise RuntimeError("No API key found")
        self.http_model = http_model
        self.websocket_model = websocket_model
        self.temperature = temperature

        # WebSocket session state
        self._session = None
        self._connection = None

    def _create_client(self, api_key: str):
        """Create Gemini client for given API key."""
        import google.genai as genai

        return genai.Client(api_key=api_key)

    async def generate(self, messages: list[dict]) -> str:
        """One-shot completion with full conversation context."""

        async def _generate_with_key(api_key: str) -> str:
            try:
                import google.genai as genai

                client = self._create_client(api_key)
                response = await client.aio.models.generate_content(
                    model=self.http_model,
                    contents=self._convert_messages_to_gemini_format(messages),
                    config=genai.types.GenerateContentConfig(
                        temperature=self.temperature,
                        max_output_tokens=8192,
                    ),
                )
                return response.text
            except ImportError as e:
                raise ImportError("Please install google-genai: pip install google-genai") from e
            except Exception as e:
                raise RuntimeError(f"Gemini Generate Error: {str(e)}") from e

        return await with_rotation("GEMINI", _generate_with_key)

    @interruptible
    async def stream(self, messages: list[dict]) -> AsyncGenerator[str, None]:
        """HTTP streaming with full conversation context."""

        async def _stream_with_key(api_key: str):
            import google.genai as genai

            client = self._create_client(api_key)
            return await client.aio.models.generate_content_stream(
                model=self.http_model,
                contents=self._convert_messages_to_gemini_format(messages),
                config=genai.types.GenerateContentConfig(
                    temperature=self.temperature,
                    max_output_tokens=8192,
                ),
            )

        # Get streaming response with rotation
        response = await with_rotation("GEMINI", _stream_with_key)

        # Stream provider-native chunks - pure pipe
        async for chunk in response:
            if chunk.text:
                yield chunk.text

    async def connect(self, messages: list[dict]) -> "Gemini":
        """Create session with initial context. Returns session-enabled Gemini instance."""

        try:
            from google.genai import types

            # Force rotation to get fresh key for this session
            async def _create_client_with_key(api_key: str):
                return self._create_client(api_key)

            client = await with_rotation("GEMINI", _create_client_with_key)

            # Extract system instructions for Live API
            system_instruction = ""
            for msg in messages:
                if msg["role"] == "system":
                    system_instruction += msg["content"] + "\n"

            config = types.LiveConnectConfig(
                response_modalities=["TEXT"],
                system_instruction=system_instruction.strip() if system_instruction else None,
            )
            connection = client.aio.live.connect(model=self.websocket_model, config=config)
            session = await connection.__aenter__()

            # Load initial conversation context (skip system instructions for Live API)
            for msg in messages:
                if msg["role"] != "system":  # Live API uses systemInstruction separately
                    await session.send_client_content(
                        turns=types.Content(
                            role=msg["role"], parts=[types.Part(text=msg["content"])]
                        ),
                        turn_complete=True,
                    )

                    # Drain any responses to initial context
                    await self._drain_turn_with_dual_signals(session)

            # Create session-enabled instance with fresh rotated key
            fresh_key = get_api_key("gemini")  # Force fresh rotation
            session_instance = Gemini(
                api_key=fresh_key,
                http_model=self.http_model,
                websocket_model=self.websocket_model,
                temperature=self.temperature,
            )
            session_instance._session = session
            session_instance._connection = connection

            return session_instance

        except Exception as e:
            logger.warning(f"Gemini WebSocket connection failed: {e}")
            raise RuntimeError(f"Gemini connection failed: {e}") from e

    async def send(self, content: str) -> AsyncGenerator[str, None]:
        """Send message in session and stream response until turn completion."""
        if not self._session:
            raise RuntimeError("send() requires active session. Call connect() first.")

        try:
            from google.genai import types

            # Send user message
            await self._session.send_client_content(
                turns=types.Content(role="user", parts=[types.Part(text=content)]),
                turn_complete=True,
            )

            # Stream response with DUAL SIGNAL fix - the critical empirical discovery
            seen_generation_complete = False
            message_count = 0

            async for message in self._session.receive():
                message_count += 1

                if hasattr(message, "server_content") and message.server_content:
                    sc = message.server_content

                    # Collect text from model_turn.parts
                    if (
                        hasattr(sc, "model_turn")
                        and sc.model_turn
                        and hasattr(sc.model_turn, "parts")
                    ):
                        for part in sc.model_turn.parts:
                            if hasattr(part, "text") and part.text:
                                yield part.text

                    # Track generation_complete signal
                    if hasattr(sc, "generation_complete") and sc.generation_complete:
                        seen_generation_complete = True

                    # CRITICAL DUAL SIGNAL FIX: Break only when we've seen BOTH signals
                    if (
                        seen_generation_complete
                        and hasattr(sc, "turn_complete")
                        and sc.turn_complete
                    ):
                        return  # Provider infrastructure turn completion

                # Safety limit
                if message_count > 100:
                    logger.warning("Gemini session hit message limit")
                    return

        except Exception as e:
            logger.warning(f"Gemini session send failed: {e}")
            return

    async def close(self) -> None:
        """Close session and cleanup resources."""
        if not self._connection:
            return  # No-op for HTTP-only instances

        try:
            await self._connection.__aexit__(None, None, None)
            self._session = None
            self._connection = None
        except Exception as e:
            logger.warning(f"Gemini session close failed: {e}")

    async def _drain_turn_with_dual_signals(self, session):
        """Drain turn using dual signal pattern without yielding content."""
        seen_generation_complete = False
        message_count = 0

        async for message in session.receive():
            message_count += 1

            if hasattr(message, "server_content") and message.server_content:
                sc = message.server_content

                # Track generation_complete signal
                if hasattr(sc, "generation_complete") and sc.generation_complete:
                    seen_generation_complete = True

                # Break only when we've seen BOTH signals
                if seen_generation_complete and hasattr(sc, "turn_complete") and sc.turn_complete:
                    return

            # Safety limit
            if message_count > 100:
                return

    def _convert_messages_to_gemini_format(self, messages: list[dict]) -> list:
        """Convert standard message format to Gemini's expected format."""
        from google.genai import types

        contents = []
        for msg in messages:
            # Handle system messages as user messages with context
            role = "user" if msg["role"] == "system" else msg["role"]
            content = msg["content"]

            # For system messages, prefix with context indicator
            if msg["role"] == "system":
                content = f"System: {content}"

            contents.append(types.Content(role=role, parts=[types.Part(text=content)]))

        return contents
