from typing import AsyncIterator, Dict, List, Union

try:
    from mistralai import Mistral
except ImportError:
    raise ImportError("Mistral support not installed. Use `pip install cogency[mistral]`") from None

from cogency.constants import MAX_TOKENS
from cogency.llm.base import BaseLLM
from cogency.resilience import safe


class MistralLLM(BaseLLM):
    def __init__(
        self,
        api_keys: Union[str, List[str]] = None,
        model: str = "mistral-large-latest",
        timeout: float = 15.0,
        temperature: float = 0.7,
        max_tokens: int = MAX_TOKENS,
        max_retries: int = 3,
        **kwargs,
    ):
        super().__init__("mistral", api_keys)
        self.model = model

        # Configuration parameters
        self.timeout = timeout
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.max_retries = max_retries

        # Build kwargs for Mistral client
        self.kwargs = {
            "temperature": temperature,
            "max_tokens": max_tokens,
            **kwargs,
        }

    def _get_client(self):
        """Get client instance with current API key."""
        key = self.next_key()
        return Mistral(api_key=key)

    @safe()
    async def run(self, messages: List[Dict[str, str]], **kwargs) -> str:
        client = self._get_client()
        mistral_messages = self._format(messages)

        res = await client.chat.complete_async(
            model=self.model,
            messages=mistral_messages,
            **self.kwargs,
            **kwargs,
        )
        return res.choices[0].message.content

    @safe()
    async def stream(self, messages: List[Dict[str, str]], **kwargs) -> AsyncIterator[str]:
        client = self._get_client()
        mistral_messages = self._format(messages)

        stream = await client.chat.stream_async(
            model=self.model,
            messages=mistral_messages,
            **self.kwargs,
            **kwargs,
        )

        async for chunk in stream:
            if chunk.data.choices[0].delta.content:
                yield chunk.data.choices[0].delta.content
