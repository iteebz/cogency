from typing import AsyncIterator, Dict, List, Optional, Union

import anthropic

from cogency.llm.base import BaseLLM
from cogency.llm.key_rotator import KeyRotator
from cogency.utils.interrupt import interruptable
from cogency.utils.errors import ConfigurationError


class AnthropicLLM(BaseLLM):
    def __init__(
        self,
        api_keys: Union[str, List[str]] = None,
        model: str = "claude-3-5-sonnet-20241022",
        timeout: float = 15.0,
        temperature: float = 0.7,
        max_tokens: int = 4096,
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
        self.max_tokens = max_tokens
        self.max_retries = max_retries

        # Build kwargs for Anthropic client
        self.kwargs = {
            "timeout": timeout,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "max_retries": max_retries,
            **kwargs,
        }

        self._client: Optional[anthropic.AsyncAnthropic] = None
        self._init_client()  # Initialize the client

    def _init_client(self):
        """Initializes the Anthropic client based on the active key."""
        current_key = self.key_rotator.get_key() if self.key_rotator else self.api_key

        if not current_key:
            raise ConfigurationError(
                "API key must be provided either directly or via KeyRotator.",
                error_code="NO_CURRENT_API_KEY",
            )

        self._client = anthropic.AsyncAnthropic(api_key=current_key)

    @interruptable
    async def invoke(self, messages: List[Dict[str, str]], **kwargs) -> str:
        # Rotate key and update current LLM if a rotator is used
        if self.key_rotator:
            self._init_client()

        if not self._client:
            raise RuntimeError("Anthropic client not initialized.")

        # Convert messages to Anthropic format
        anthropic_messages = []
        for msg in messages:
            anthropic_messages.append({"role": msg["role"], "content": msg["content"]})

        res = await self._client.messages.create(
            model=self.model,
            messages=anthropic_messages,
            **self.kwargs,
            **kwargs,
        )
        return res.content[0].text

    async def stream(self, messages: List[Dict[str, str]], yield_interval: float = 0.0, **kwargs) -> AsyncIterator[str]:
        # Rotate key and update current LLM if a rotator is used
        if self.key_rotator:
            self._init_client()

        if not self._client:
            raise RuntimeError("Anthropic client not initialized.")

        # Convert messages to Anthropic format
        anthropic_messages = []
        for msg in messages:
            anthropic_messages.append({"role": msg["role"], "content": msg["content"]})

        async with self._client.messages.stream(
            model=self.model,
            messages=anthropic_messages,
            **self.kwargs,
            **kwargs,
        ) as stream:
            async for text in stream.text_stream:
                yield text