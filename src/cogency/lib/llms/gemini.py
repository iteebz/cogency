"""Gemini provider - LLM protocol implementation."""

from ...core.protocols import LLM, Event
from ...core.result import Err, Ok, Result
from ..rotation import rotate


class Gemini(LLM):
    """Gemini provider implementing LLM protocol."""

    def __init__(
        self,
        api_key: str = None,
        llm_model: str = "gemini-2.5-flash-lite",
        stream_model: str = "models/gemini-2.5-flash-live-preview",
        temperature: float = 0.7,
    ):
        from ..credentials import detect_api_key

        self.api_key = api_key or detect_api_key("gemini")
        self.llm_model = llm_model
        self.stream_model = stream_model
        self.temperature = temperature
        # Session resume capability
        self.resumable = True

    def _create_client(self, api_key: str):
        """Create Gemini client for given API key."""
        import google.genai as genai

        return genai.Client(api_key=api_key)

    @rotate
    async def generate(self, client, messages: list[dict]) -> Result[str]:
        """Generate complete response from conversation messages."""
        import logging

        logger = logging.getLogger(__name__)

        try:
            prompt = "\n".join([f"{msg['role']}: {msg['content']}" for msg in messages])

            response = await client.aio.models.generate_content(
                model=self.llm_model, contents=prompt
            )

            response_text = response.text
            logger.debug(f"GEMINI HTTP GENERATE: {response_text}")
            logger.debug(f"GEMINI HTTP CONTAINS §CALLS: {'§CALLS' in response_text}")
            logger.debug(f"GEMINI HTTP CONTAINS §THINK: {'§THINK' in response_text}")
            logger.debug(f"GEMINI HTTP CONTAINS §END: {'§END' in response_text}")

            return Ok(response_text)

        except ImportError:
            return Err("Please install google-genai: pip install google-genai")
        except Exception as e:
            logger.debug(f"GEMINI ERROR: {str(e)}")
            return Err(f"Gemini Generate Error: {str(e)}")

    async def connect(self, messages: list[dict]):
        """Create bidirectional Gemini Live WebSocket session."""
        try:
            from google.genai import types

            config = {
                "response_modalities": ["TEXT"],
                "generation_config": {"max_output_tokens": 8192},
            }

            client = self._create_client(self.api_key)
            connection = client.aio.live.connect(model=self.stream_model, config=config)
            session = await connection.__aenter__()

            # Send initial conversation
            content = "\n".join([f"{msg['role']}: {msg['content']}" for msg in messages])
            await session.send_client_content(
                turns=types.Content(role="user", parts=[types.Part(text=content)]),
                turn_complete=True,
            )

            return {"session": session, "connection": connection, "types": types}

        except Exception:
            return None

    async def send(self, session, content: str) -> bool:
        """Send content to Gemini Live session."""
        if not session:
            return False

        try:
            types = session["types"]
            await session["session"].send_client_content(
                turns=types.Content(role="user", parts=[types.Part(text=content)]),
                turn_complete=True,
            )
            return True
        except Exception:
            return False

    async def receive(self, session):
        """Receive streaming tokens from Gemini Live session until turn completion."""
        if not session:
            return

        try:
            async for message in session["session"].receive():
                try:
                    for part in message.server_content.model_turn.parts:
                        if part.text:
                            yield part.text
                except AttributeError:
                    if hasattr(message, "server_content") and (
                        (
                            hasattr(message.server_content, "turn_complete")
                            and message.server_content.turn_complete
                        )
                        or (
                            hasattr(message.server_content, "generation_complete")
                            and message.server_content.generation_complete
                        )
                    ):
                        from ...core.protocols import Event

                        yield Event.YIELD.delimiter
                        return
        except Exception:
            return

    async def close(self, session) -> bool:
        """Close Gemini Live session."""
        if not session:
            return False
        try:
            await session["connection"].__aexit__(None, None, None)
            return True
        except Exception:
            return False

    @rotate
    async def stream(self, client, messages: list[dict]):
        """Generate streaming tokens from conversation messages."""
        import logging

        logger = logging.getLogger(__name__)

        try:
            prompt = "\n".join([f"{msg['role']}: {msg['content']}" for msg in messages])

            # GENUINE STREAMING: Await the coroutine first, then iterate
            stream = await client.aio.models.generate_content_stream(
                model=self.llm_model, contents=prompt
            )

            async for chunk in stream:
                if chunk.text:
                    logger.debug(f"GEMINI HTTP STREAM CHUNK: {repr(chunk.text)}")
                    yield Ok(chunk.text)

            # HTTP stream ended - inject YIELD to trigger tool execution (like WebSocket turn_complete)
            logger.debug("GEMINI HTTP STREAM COMPLETE - injecting YIELD delimiter")
            yield Ok(Event.YIELD.delimiter)

        except ImportError:
            yield Err("Please install google-genai: pip install google-genai")
        except Exception as e:
            yield Err(f"Gemini Stream Error: {str(e)}")
