"""OpenAI provider - LLM protocol implementation."""

from ...core.protocols import LLM
from ...core.result import Ok, Result
from ..logger import logger
from ..rotation import rotate
from .error_handling import handle_generate_errors, handle_stream_errors


class OpenAI(LLM):
    """OpenAI provider implementing LLM protocol."""

    def __init__(
        self,
        api_key: str = None,
        llm_model: str = "gpt-4o-mini",
        stream_model: str = "gpt-4o-mini-realtime-preview",
        temperature: float = 1.0,
        max_tokens: int = 500,
    ):
        # Explicit dotenv loading with override=True to handle empty environment variables
        from dotenv import load_dotenv

        load_dotenv(override=True)

        from ..credentials import detect_api_key

        # Get API key
        self.api_key = api_key or detect_api_key("openai")
        if not self.api_key:
            raise RuntimeError("No API key found")
        self.llm_model = llm_model
        self.stream_model = stream_model
        self.temperature = temperature
        self.max_tokens = max_tokens

        # Session resume capability
        self.resumable = True

    def _create_client(self, api_key: str):
        """Create OpenAI client for given API key."""
        import openai

        return openai.AsyncOpenAI(api_key=api_key)

    @rotate
    @handle_generate_errors("OpenAI", "openai")
    async def generate(self, client, messages: list[dict]) -> Result[str]:
        """Generate complete response from conversation messages."""
        response = await client.chat.completions.create(
            model=self.llm_model,
            messages=messages,
            max_completion_tokens=self.max_tokens,
            temperature=self.temperature,
            stream=False,
        )

        return Ok(response.choices[0].message.content)

    async def connect(self, messages: list[dict]):
        """Create bidirectional OpenAI Realtime session via SDK WebSocket."""
        return await self._do_connect(messages)

    async def _do_connect(self, messages: list[dict]):
        """Internal connection logic with timeout protection."""
        try:
            import openai

            client = openai.AsyncOpenAI(api_key=self.api_key)
            connection = await client.beta.realtime.connect(model=self.stream_model).__aenter__()

            # Configure for text responses
            await connection.session.update(
                session={
                    "modalities": ["text"],
                    "temperature": self.temperature,
                    "max_response_output_tokens": 2000,
                    "instructions": messages[0]["content"] if messages else "",
                }
            )

            # Send initial conversation
            content = "\n".join([f"{msg['role']}: {msg['content']}" for msg in messages[1:]])
            if content:
                await connection.conversation.item.create(
                    item={
                        "type": "message",
                        "role": "user",
                        "content": [{"type": "input_text", "text": content}],
                    }
                )
                await connection.response.create()

            return connection

        except Exception as e:
            logger.warning(f"OpenAI WebSocket connection failed: {e}")
            return None

    async def send(self, session, content: str, messages=None) -> bool:
        """Send content to OpenAI Realtime session."""
        if not session:
            return False

        try:
            await session.conversation.item.create(
                item={
                    "type": "message",
                    "role": "user",
                    "content": [{"type": "input_text", "text": content}],
                }
            )
            await session.response.create()
            return True
        except Exception as e:
            logger.warning(f"OpenAI WebSocket send failed: {e}")
            return False

    async def receive(self, session):
        """Receive streaming tokens from OpenAI Realtime session until turn completion."""
        import time

        if not session:
            return

        try:
            start_time = time.time()
            async for event in session:
                # Check timeout manually
                if time.time() - start_time > 15:
                    logger.warning("OpenAI WebSocket receive timeout after 15s")
                    break
                if event.type == "response.text.delta" and event.delta:
                    yield event.delta
                elif event.type == "response.done" or event.type == "error":
                    from ...core.protocols import Event

                    yield Event.YIELD.delimiter
                    break  # Use break, not return - keeps connection alive
        except Exception as e:
            logger.warning(f"OpenAI WebSocket receive failed: {e}")
            return

    async def close(self, session) -> bool:
        """Close OpenAI Realtime session with timeout protection."""
        if not session:
            return False
        try:
            import asyncio

            # Force cleanup with timeout to prevent resource leaks
            await asyncio.wait_for(session.close(), timeout=5.0)
            return True
        except asyncio.TimeoutError:
            logger.warning("OpenAI WebSocket close timeout - forcing cleanup")
            return False
        except Exception as e:
            logger.warning(f"OpenAI WebSocket close failed: {e}")
            return False

    @rotate
    @handle_stream_errors("OpenAI", "openai")
    async def stream(self, client, messages: list[dict]):
        """Generate streaming tokens from conversation messages."""
        response = await client.chat.completions.create(
            model=self.llm_model,
            messages=messages,
            max_completion_tokens=self.max_tokens,
            temperature=self.temperature,
            stream=True,
        )

        async for chunk in response:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
