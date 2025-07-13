from typing import AsyncIterator, Dict, List, Optional, Union

import openai

from cogency.llm.base import BaseLLM
from cogency.llm.key_rotator import KeyRotator
from cogency.utils.interrupt import interruptable
from cogency.utils.errors import ConfigurationError


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
        # Validate inputs
        if not api_keys:
            raise ConfigurationError("API keys must be provided", error_code="NO_API_KEYS")

        # Handle the cleaner interface: if list provided, create key rotator internally
        if isinstance(api_keys, list) and len(api_keys) > 1:
            key_rotator = KeyRotator(api_keys)
            api_key = None
        elif isinstance(api_keys, list) and len(api_keys) == 1:
            key_rotator = None
            api_key = api_keys[0]
        else:
            key_rotator = None
            api_key = api_keys

        super().__init__(api_key, key_rotator)
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
        current_key = self.key_rotator.get_key() if self.key_rotator else self.api_key

        if not current_key:
            raise ConfigurationError(
                "API key must be provided either directly or via KeyRotator.",
                error_code="NO_CURRENT_API_KEY",
            )

        self._client = openai.AsyncOpenAI(
            api_key=current_key,
            base_url="https://api.x.ai/v1"
        )

    @interruptable
    async def invoke(self, messages: List[Dict[str, str]], **kwargs) -> str:
        # Rotate key and update current LLM if a rotator is used
        if self.key_rotator:
            self._init_client()

        if not self._client:
            raise RuntimeError("Grok client not initialized.")

        # Convert messages to OpenAI format (Grok uses OpenAI-compatible API)
        grok_messages = []
        for msg in messages:
            grok_messages.append({"role": msg["role"], "content": msg["content"]})

        res = await self._client.chat.completions.create(
            model=self.model,
            messages=grok_messages,
            **self.kwargs,
            **kwargs,
        )
        return res.choices[0].message.content

    async def stream(self, messages: List[Dict[str, str]], yield_interval: float = 0.0, **kwargs) -> AsyncIterator[str]:
        # Rotate key and update current LLM if a rotator is used
        if self.key_rotator:
            self._init_client()

        if not self._client:
            raise RuntimeError("Grok client not initialized.")

        # Convert messages to OpenAI format (Grok uses OpenAI-compatible API)
        grok_messages = []
        for msg in messages:
            grok_messages.append({"role": msg["role"], "content": msg["content"]})

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