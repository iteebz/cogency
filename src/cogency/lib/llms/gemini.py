import logging
from collections.abc import AsyncGenerator
from typing import Any

from cogency.core.protocols import LLM

from .interrupt import interruptible
from .rotation import get_api_key, with_rotation

logger = logging.getLogger(__name__)

MAX_SESSION_MESSAGES = 1000


class Gemini(LLM):
    """Gemini provider with HTTP streaming and WebSocket (Live API) support.

    Implements dual-signal completion detection for 100% reliability:
    - generation_complete: Content generation finished
    - turn_complete: Turn interaction finished
    Both signals required to prevent premature stream termination.
    """

    def __init__(
        self,
        api_key: str | None = None,
        http_model: str = "gemini-2.5-flash",
        websocket_model: str = "gemini-2.5-flash-live-preview",
        temperature: float = 0.7,
    ):
        self.api_key = api_key or get_api_key("gemini")
        if not self.api_key:
            raise ValueError("No API key found")
        self.http_model = http_model
        self.websocket_model = websocket_model
        self.temperature = temperature

        # WebSocket session state
        self._session: Any = None
        self._connection: Any = None

    def _create_client(self, api_key: str):
        import google.genai as genai

        return genai.Client(api_key=api_key)

    async def generate(self, messages: list[dict[str, Any]]) -> str:
        async def _generate_with_key(api_key: str) -> str:
            try:
                import google.genai as genai

                client = self._create_client(api_key)
                aclient = client.aio
                response = await aclient.models.generate_content(  # type: ignore[reportUnknownMemberType]
                    model=self.http_model,
                    contents=self._convert_messages_to_gemini_format(messages),
                    config=genai.types.GenerateContentConfig(
                        temperature=self.temperature,
                        max_output_tokens=4096,
                    ),
                )
                return response.text or ""
            except ImportError as e:
                raise ImportError("Please install google-genai: pip install google-genai") from e

        return await with_rotation("GEMINI", _generate_with_key)

    @interruptible
    async def stream(self, messages: list[dict[str, Any]]) -> AsyncGenerator[str, None]:
        async def _stream_with_key(api_key: str):
            import google.genai as genai

            client = self._create_client(api_key)
            aclient = client.aio
            return await aclient.models.generate_content_stream(  # type: ignore[reportUnknownMemberType]
                model=self.http_model,
                contents=self._convert_messages_to_gemini_format(messages),
                config=genai.types.GenerateContentConfig(
                    temperature=self.temperature,
                    max_output_tokens=4096,
                ),
            )

        # Get streaming response with rotation
        response = await with_rotation("GEMINI", _stream_with_key)

        # Stream provider-native chunks - pure pipe
        async for chunk in response:
            if chunk.text:
                yield chunk.text

    async def connect(self, messages: list[dict[str, Any]]) -> "Gemini":
        try:
            from google.genai import types

            used_key = None

            async def _create_client_with_key(api_key: str):
                nonlocal used_key
                used_key = api_key
                return self._create_client(api_key)

            client = await with_rotation("GEMINI", _create_client_with_key)

            # Extract system instructions for Live API
            system_instruction = ""
            for msg in messages:
                if msg["role"] == "system":
                    system_instruction += msg["content"] + "\n"

            config = types.LiveConnectConfig(
                response_modalities=["TEXT"],  # type: ignore[list-item]
                system_instruction=system_instruction.strip() if system_instruction else "",
            )
            connection = client.aio.live.connect(model=self.websocket_model, config=config)
            session = await connection.__aenter__()

            # Load conversation history (skip system and last user message)
            # Last user message will be sent via send() to trigger generation
            non_system_msgs = [m for m in messages if m["role"] != "system"]
            history_msgs = (
                non_system_msgs[:-1]
                if non_system_msgs and non_system_msgs[-1]["role"] == "user"
                else non_system_msgs
            )

            for msg in history_msgs:
                # Gemini uses "model" not "assistant"
                role = "model" if msg["role"] == "assistant" else msg["role"]
                await session.send_client_content(
                    turns=types.Content(role=role, parts=[types.Part(text=msg["content"])]),
                    turn_complete=True,
                )
                # Drain any responses to initial context
                await self._drain_turn_with_dual_signals(session)

            session_instance = Gemini(
                api_key=used_key,
                http_model=self.http_model,
                websocket_model=self.websocket_model,
                temperature=self.temperature,
            )
            session_instance._session = session
            session_instance._connection = connection

            return session_instance
        except Exception as e:
            logger.warning(f"Gemini connection failed: {e}")
            raise RuntimeError("Gemini connection failed") from e

    async def send(self, content: str) -> AsyncGenerator[str, None]:  # noqa: C901  # Gemini protocol adapter with dual-signal streaming
        if not self._session:
            raise RuntimeError("send() requires active session. Call connect() first.")

        try:
            from google.genai import types

            # Send user message
            await self._session.send_client_content(
                turns=types.Content(role="user", parts=[types.Part(text=content)]),
                turn_complete=True,
            )
        except Exception as e:
            logger.error(f"Error sending message in Gemini session: {e}")

        # Stream response with DUAL SIGNAL fix - the critical empirical discovery

        seen_generation_complete = False

        message_count = 0

        async for message in self._session.receive():
            message_count += 1

            if hasattr(message, "server_content") and message.server_content:
                sc = message.server_content

                # Collect text from model_turn.parts
                if hasattr(sc, "model_turn") and sc.model_turn and hasattr(sc.model_turn, "parts"):
                    for part in sc.model_turn.parts:
                        if hasattr(part, "text") and part.text:
                            yield part.text

                # Track generation_complete signal
                if hasattr(sc, "generation_complete") and sc.generation_complete:
                    seen_generation_complete = True

                # Wait for both Gemini stream completion signals
                if seen_generation_complete and hasattr(sc, "turn_complete") and sc.turn_complete:
                    return

            if message_count > MAX_SESSION_MESSAGES:
                logger.error(
                    f"Gemini session exceeded {MAX_SESSION_MESSAGES} messages without completion signals. "
                    "This indicates a protocol violation or infinite loop."
                )
                return

    async def close(self) -> None:
        if not self._connection:
            return  # No-op for HTTP-only instances

        await self._connection.__aexit__(None, None, None)
        self._session = None
        self._connection = None

    async def _drain_turn_with_dual_signals(self, session: Any) -> None:
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

            if message_count > MAX_SESSION_MESSAGES:
                return

    def _convert_messages_to_gemini_format(self, messages: list[dict[str, Any]]) -> list[Any]:
        from google.genai import types

        contents: list[Any] = []
        for msg in messages:
            if msg["role"] == "assistant":
                role = "model"
                content = msg["content"]
            elif msg["role"] == "system":
                continue  # System messages are handled by system_instruction in Live API
            else:
                role = msg["role"]
                content = msg["content"]

            contents.append(types.Content(role=role, parts=[types.Part(text=content)]))

        return contents
