"""OpenAI provider - LLM protocol implementation."""

from ...core.protocols import LLM, Event
from ...core.result import Err, Ok, Result
from ..rotation import rotate


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
        from ..credentials import detect_api_key

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
    async def generate(self, client, messages: list[dict]) -> Result[str]:
        """Generate complete response from conversation messages."""
        try:
            response = await client.chat.completions.create(
                model=self.llm_model,
                messages=messages,
                max_completion_tokens=self.max_tokens,
                temperature=self.temperature,
                stream=False,
            )

            return Ok(response.choices[0].message.content)

        except ImportError:
            return Err("Please install openai: pip install openai")
        except Exception as e:
            return Err(f"OpenAI Generate Error: {str(e)}")

    async def connect(self, messages: list[dict]):
        """Create bidirectional OpenAI Realtime session via SDK WebSocket."""
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

        except Exception:
            return None

    async def send(self, session, content: str) -> bool:
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
        except Exception:
            return False

    async def receive(self, session):
        """Receive streaming tokens from OpenAI Realtime session until turn completion."""
        if not session:
            return

        try:
            async for event in session:
                if event.type == "response.text.delta" and event.delta:
                    yield event.delta
                elif event.type == "response.done" or event.type == "error":
                    from ...core.protocols import Event

                    yield Event.YIELD.delimiter
                    return
        except Exception:
            return

    async def close(self, session) -> bool:
        """Close OpenAI Realtime session."""
        if not session:
            return False
        try:
            await session.close()
            return True
        except Exception:
            return False

    @rotate
    async def stream(self, client, messages: list[dict]):
        """Generate streaming tokens from conversation messages."""
        try:
            response = await client.chat.completions.create(
                model=self.llm_model,
                messages=messages,
                max_completion_tokens=self.max_tokens,
                temperature=self.temperature,
                stream=True,
            )

            async for chunk in response:
                if chunk.choices[0].delta.content:
                    import logging

                    logger = logging.getLogger(__name__)
                    logger.debug(
                        f"OPENAI HTTP STREAM CHUNK: {repr(chunk.choices[0].delta.content)}"
                    )
                    yield Ok(chunk.choices[0].delta.content)

            # HTTP stream ended - inject YIELD to trigger tool execution (like WebSocket response.done)
            import logging

            logger = logging.getLogger(__name__)
            logger.debug("OPENAI HTTP STREAM COMPLETE - injecting YIELD delimiter")
            yield Ok(Event.YIELD.delimiter)

        except ImportError:
            yield Err("Please install openai: pip install openai")
        except Exception as e:
            yield Err(f"OpenAI Stream Error: {str(e)}")
