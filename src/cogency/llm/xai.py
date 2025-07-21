from typing import AsyncIterator, Dict, List, Optional, Union

try:
    import openai
except ImportError:
    raise ImportError("OpenAI support not installed (required for xAI OpenAI-compatible API). Use `pip install cogency[openai]`")

from cogency.llm.base import BaseLLM
from cogency.utils.keys import KeyManager
from cogency.errors import ConfigurationError
from cogency.resilience import safe


class xAILLM(BaseLLM):
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
        self.keys = KeyManager.for_provider("xai", api_keys)
        super().__init__(self.keys.api_key, self.keys.key_rotator)
        self.model = model

        # Configuration parameters
        self.timeout = timeout
        self.temperature = temperature
        self.max_retries = max_retries

        # Build kwargs for xAI client
        self.kwargs = {
            "temperature": temperature,
            **kwargs,
        }
        self.client_kwargs = {
            "timeout": timeout,
            "max_retries": max_retries,
        }

        self._client: Optional[openai.AsyncOpenAI] = None
        self._init_client()  # Initialize the client

    def _init_client(self):
        """Initializes the xAI client based on the active key."""
        current_key = self._ensure_current_key()
        self._client = openai.AsyncOpenAI(
            api_key=current_key,
            base_url="https://api.x.ai/v1",
            **self.client_kwargs
        )

    def _get_client(self):
        """Get client instance."""
        return self._client

    def _rotate_client(self):
        """Rotate to the next key and re-initialize the client."""
        if self.keys.has_multiple():
            self._init_client()


    @safe()
    async def invoke(self, messages: List[Dict[str, str]], **kwargs) -> str:
        self._rotate_client()
        xai_messages = self._convert_msgs(messages)

        res = await self._client.chat.completions.create(
            model=self.model,
            messages=xai_messages,
            **self.kwargs,
            **kwargs,
        )
        return res.choices[0].message.content

    @safe()
    async def stream(self, messages: List[Dict[str, str]], yield_interval: float = 0.0, **kwargs) -> AsyncIterator[str]:
        self._rotate_client()
        xai_messages = self._convert_msgs(messages)

        stream = await self._client.chat.completions.create(
            model=self.model,
            messages=xai_messages,
            stream=True,
            **self.kwargs,
            **kwargs,
        )

        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
