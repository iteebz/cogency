"""OpenAI provider - LLM protocol implementation."""

from ...core.protocols import LLM
from ..logger import logger
from ..rotation import rotate
from .interrupt import interruptible


class OpenAI(LLM):
    """OpenAI provider implementing LLM protocol."""

    def __init__(
        self,
        api_key: str = None,
        llm_model: str = "gpt-4o-mini",
        stream_model: str = "gpt-4o-mini-realtime-preview",  # Note: Full gpt-4o-realtime-preview supports delimiters better
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

    def _create_client(self, api_key: str):
        """Create OpenAI client for given API key."""
        import openai

        return openai.AsyncOpenAI(api_key=api_key)

    @rotate
    async def generate(self, client, messages: list[dict]) -> str:
        """Generate complete response from conversation messages."""
        try:
            response = await client.chat.completions.create(
                model=self.llm_model,
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

    async def connect(self, messages: list[dict]):
        """Create bidirectional OpenAI Realtime session via SDK WebSocket."""
        try:
            import openai

            client = openai.AsyncOpenAI(api_key=self.api_key)
            connection_manager = client.beta.realtime.connect(model=self.stream_model)
            connection = await connection_manager.__aenter__()

            # Store connection manager for proper cleanup
            connection._connection_manager = connection_manager

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

            # CRITICAL: Trigger response generation for resume mode compatibility
            if user_messages:
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

    @interruptible
    async def receive(self, session):
        """Receive streaming tokens from OpenAI Realtime session until turn completion."""
        import time

        if not session:
            return

        start_time = time.time()
        async for event in session:
            # Check timeout manually
            if time.time() - start_time > 15:
                logger.warning("OpenAI WebSocket receive timeout after 15s")
                break
            if event.type == "response.text.delta" and event.delta:
                yield event.delta
            elif event.type == "response.done" or event.type == "error":
                yield "§EXECUTE"  # Protocol boundary for tool execution
                break  # Use break, not return - keeps connection alive

    async def close(self, session) -> bool:
        """Close OpenAI Realtime session with timeout protection."""
        if not session:
            return False
        try:
            import asyncio

            # Use proper context manager cleanup if available
            if hasattr(session, "_connection_manager"):
                await asyncio.wait_for(
                    session._connection_manager.__aexit__(None, None, None), timeout=5.0
                )
            else:
                # Fallback to direct close
                await asyncio.wait_for(session.close(), timeout=5.0)
            return True
        except asyncio.TimeoutError:
            logger.warning("OpenAI WebSocket close timeout - forcing cleanup")
            return False
        except Exception as e:
            logger.warning(f"OpenAI WebSocket close failed: {e}")
            return False

    @rotate
    @interruptible
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
                content = chunk.choices[0].delta.content
                # Character-level streaming for maximum responsiveness
                for char in content:
                    yield char

        # Stream complete - emit EXECUTE for tool execution
        yield "§EXECUTE"
