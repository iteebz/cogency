from typing import AsyncIterator, Dict, List, Optional, Union

try:
    import openai
except ImportError:
    raise ImportError("OpenAI support not installed (required for Grok). Use `pip install cogency[openai]`")

from cogency.llm.base import BaseLLM
from cogency.utils.keys import KeyManager
from cogency.errors import ConfigurationError


class GrokLLM(BaseLLM):
    def __init__(
        self,
        api_keys: Union[str, List[str]] = None,
        model: str = "grok-beta",
        timeout: float = 15.0,
        temperature: float = 0.7,
        max_retries: int = 3,
        **kwargs,
    ):
        # Beautiful unified key management - auto-detects, handles all scenarios
        self.keys = KeyManager.for_provider("grok", api_keys)
        super().__init__(self.keys.api_key, self.keys.key_rotator)
        self.model = model

        # Configuration parameters
        self.timeout = timeout
        self.temperature = temperature
        self.max_retries = max_retries

        # Build kwargs for Grok client
        self.kwargs = {
            "timeout": timeout,
            "temperature": temperature,
            "max_retries": max_retries,
            **kwargs,
        }

        self._client: Optional[openai.AsyncOpenAI] = None
        self._init_client()  # Initialize the client

    def _init_client(self):
        """Initializes the Grok client based on the active key."""
        current_key = self.keys.get_current()

        if not current_key:
            raise ConfigurationError(
                "API key must be provided either directly or via KeyRotator.",
                error_code="NO_CURRENT_API_KEY",
            )

        self._client = openai.AsyncOpenAI(
            api_key=current_key,
            base_url="https://api.x.ai/v1"
        )

    def _get_client(self):
        """Get client instance."""
        return self._client

    def _rotate_client(self):
        """Rotate to the next key and re-initialize the client."""
        if self.keys.has_multiple():
            self._init_client()

    def _convert_msgs(self, msgs: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Convert to provider format."""
        return [{"role": m["role"], "content": m["content"]} for m in msgs]

    async def invoke(self, messages: List[Dict[str, str]], **kwargs) -> str:
        self._rotate_client()
        grok_messages = self._convert_msgs(messages)

        res = await self._client.chat.completions.create(
            model=self.model,
            messages=grok_messages,
            **self.kwargs,
            **kwargs,
        )
        return res.choices[0].message.content

    async def stream(self, messages: List[Dict[str, str]], yield_interval: float = 0.0, **kwargs) -> AsyncIterator[str]:
        self._rotate_client()
        grok_messages = self._convert_msgs(messages)

        stream = await self._client.chat.completions.create(
            model=self.model,
            messages=grok_messages,
            stream=True,
            **self.kwargs,
            **kwargs,
        )

        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
