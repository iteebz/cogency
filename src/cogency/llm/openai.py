from typing import AsyncIterator, Dict, List, Optional, Union

try:
    import openai
except ImportError:
    raise ImportError("OpenAI support not installed. Use `pip install cogency[openai]`")

from cogency.llm.base import BaseLLM
from cogency.utils.keys import KeyManager
from cogency.errors import ConfigurationError
from cogency.resilience import safe


class OpenAILLM(BaseLLM):
    def __init__(
        self,
        api_keys: Union[str, List[str]] = None,
        model: str = "gpt-4o",
        timeout: float = 15.0,
        temperature: float = 0.7,
        max_retries: int = 3,
        **kwargs,
    ):
        # Beautiful unified key management - auto-detects, handles all scenarios
        self.keys = KeyManager.for_provider("openai", api_keys)
        super().__init__(self.keys.api_key, self.keys.key_rotator)
        self.model = model

        # Configuration parameters
        self.timeout = timeout
        self.temperature = temperature
        self.max_retries = max_retries

        # Build kwargs for OpenAI chat completions (filtering client-level params)
        self.kwargs = {
            "temperature": temperature,
            **kwargs,
        }
        self.client_kwargs = {
            "timeout": timeout,
            "max_retries": max_retries,
        }

        self._client: Optional[openai.AsyncOpenAI] = None
        self._init_client()

    def _init_client(self):
        """Init OpenAI client."""
        key = self._ensure_current_key()
        self._client = openai.AsyncOpenAI(api_key=key, **self.client_kwargs)

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
        msgs = self._convert_msgs(messages)
        res = await self._client.chat.completions.create(
            model=self.model,
            messages=msgs,
            **self.kwargs,
            **kwargs,
        )
        return res.choices[0].message.content

    @safe()
    async def stream(self, messages: List[Dict[str, str]], yield_interval: float = 0.0, **kwargs) -> AsyncIterator[str]:
        self._rotate_client()
        msgs = self._convert_msgs(messages)
        stream = await self._client.chat.completions.create(
            model=self.model,
            messages=msgs,
            stream=True,
            **self.kwargs,
            **kwargs,
        )
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content