"""Gemini provider - LLM protocol implementation."""

from ...core.protocols import LLM
from ..logger import logger
from ..rotation import rotate
from .interrupt import interruptible


class Gemini(LLM):
    """Gemini provider implementing LLM protocol."""

    def __init__(
        self,
        api_key: str = None,
        llm_model: str = "gemini-2.5-flash",
        stream_model: str = "gemini-2.5-flash-live-preview",
        temperature: float = 0.7,
    ):
        from ..credentials import detect_api_key

        self.api_key = api_key or detect_api_key("gemini")
        self.llm_model = llm_model
        self.stream_model = stream_model
        self.temperature = temperature

    def _prepare_websocket_config(self, messages: list[dict]) -> tuple:
        """Build WebSocket config with proper systemInstruction handling.

        Extracts system messages for systemInstruction parameter and keeps
        user/assistant messages separate.

        Returns:
            tuple: (config_dict, user_content_list)
        """
        # Extract system and user content
        system_content = []
        user_content = []

        for msg in messages:
            if msg["role"] == "system":
                system_content.append(msg["content"])
            else:  # user, assistant, etc.
                user_content.append(msg)

        # Build WebSocket config
        config = {
            "response_modalities": ["TEXT"],
            "max_output_tokens": 8192,
        }

        # Add systemInstruction if we have system content
        if system_content:
            combined = "\n\n".join(system_content)
            config["systemInstruction"] = {"parts": [{"text": combined}]}

        return config, user_content

    def _create_client(self, api_key: str):
        """Create Gemini client for given API key."""
        import google.genai as genai

        return genai.Client(api_key=api_key)

    async def _send_initial_messages(self, session, user_messages, types):
        """Send initial conversation history to WebSocket session."""
        for msg in user_messages:
            await session.send_client_content(
                turns=types.Content(role=msg["role"], parts=[types.Part(text=msg["content"])]),
                turn_complete=False,
            )
        # Complete the turn after all messages sent
        await session.send_client_content(
            turns=types.Content(role="user", parts=[types.Part(text="")]),
            turn_complete=True,
        )

    @rotate
    async def generate(self, client, messages: list[dict]) -> str:
        """Generate complete response from conversation messages."""
        try:
            # Use proper structured messages instead of flattening
            response = await client.aio.models.generate_content(
                model=self.llm_model, contents=messages
            )
            return response.text
        except ImportError as e:
            raise ImportError("Please install google-genai: pip install google-genai") from e
        except Exception as e:
            raise RuntimeError(f"Gemini Generate Error: {str(e)}") from e

    async def connect(self, messages: list[dict]):
        """Create bidirectional Gemini Live WebSocket session with rotation support."""
        from ..resilience import timeout
        from ..rotation import with_rotation

        @timeout(5)  # Balance: fast but not too fast
        async def _connect_with_key(api_key: str):
            try:
                from google.genai import types

                # Prepare WebSocket config with system instruction handling
                config_dict, user_messages = self._prepare_websocket_config(messages)

                client = self._create_client(api_key)

                # Simple connection - no resumption token ceremony needed
                config = types.LiveConnectConfig(
                    response_modalities=config_dict["response_modalities"],
                )

                # Add systemInstruction if present
                if "systemInstruction" in config_dict:
                    config.system_instruction = config_dict["systemInstruction"]

                connection = client.aio.live.connect(model=self.stream_model, config=config)
                session = await connection.__aenter__()

                # Send initial conversation history
                await self._send_initial_messages(session, user_messages, types)

                # Return simple session container
                class Session:
                    def __init__(self, session, connection, types):
                        self.session = session
                        self.connection = connection
                        self.types = types

                return Session(session, connection, types)

            except Exception as e:
                # Let with_rotation handle connection failures
                raise e

        # Let with_rotation handle all errors including quota/rate limits
        return await with_rotation("GEMINI", _connect_with_key)

    async def send(self, session, content: str) -> bool:
        """Send content to Gemini Live session."""
        if not session:
            return False

        try:
            await session.session.send_client_content(
                turns=session.types.Content(role="user", parts=[session.types.Part(text=content)]),
                turn_complete=False,  # Don't complete turn - let model continue
            )
            return True
        except Exception as e:
            logger.warning(f"Gemini WebSocket send failed: {e}")
            return False

    @interruptible
    async def receive(self, session):
        """Receive streaming tokens from Gemini Live session until turn completion."""
        import time

        if not session:
            return

        start_time = time.time()
        message_count = 0
        async for message in session.session.receive():
            message_count += 1
            logger.debug(
                f"Gemini message {message_count}: {type(message).__name__} - {repr(message)[:200]}"
            )

            # Check timeout manually
            if time.time() - start_time > 15:
                logger.warning("Gemini WebSocket receive timeout after 15s")
                break

            # Handle text content
            server_content = getattr(message, "server_content", None)
            if (
                server_content
                and hasattr(server_content, "model_turn")
                and server_content.model_turn
            ):
                model_turn = server_content.model_turn
                if hasattr(model_turn, "parts") and model_turn.parts:
                    for part in model_turn.parts:
                        if hasattr(part, "text") and part.text:
                            yield part.text

            # Handle completion signals - emit EXECUTE and break
            if server_content and (
                getattr(server_content, "turn_complete", False)
                or getattr(server_content, "generation_complete", False)
            ):
                logger.debug("Gemini turn complete")
                yield "§EXECUTE"  # Protocol boundary for tool execution
                break  # Use break, not return - keeps connection alive

        logger.debug(f"Gemini receive loop ended, processed {message_count} messages")

    async def close(self, session) -> bool:
        """Close Gemini Live session with timeout protection."""
        if not session:
            return False
        try:
            import asyncio

            # Close connection with timeout protection
            await asyncio.wait_for(session.connection.__aexit__(None, None, None), timeout=5.0)
            return True
        except asyncio.TimeoutError:
            logger.warning("Gemini WebSocket close timeout - forcing cleanup")
            return False
        except RuntimeError as e:
            # Suppress async generator cleanup noise but log other RuntimeErrors
            if "asynchronous generator is already running" in str(e):
                return True  # This is expected cleanup noise
            logger.error(f"Gemini WebSocket close RuntimeError: {e}")
            return False
        except Exception as e:
            logger.error(f"Gemini WebSocket close failed: {e}")
            return False

    @rotate
    @interruptible
    async def stream(self, client, messages: list[dict]):
        """Generate streaming tokens from conversation messages."""
        prompt = "\n".join([f"{msg['role']}: {msg['content']}" for msg in messages])

        # GENUINE STREAMING: Await the coroutine first, then iterate
        stream = await client.aio.models.generate_content_stream(
            model=self.llm_model, contents=prompt
        )

        output_text = ""
        async for chunk in stream:
            if chunk.text:
                output_text += chunk.text
                yield chunk.text
