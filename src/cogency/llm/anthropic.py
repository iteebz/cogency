from typing import AsyncIterator, Dict, List, Optional, Union

try:
    import anthropic
except ImportError:
    raise ImportError("Anthropic support not installed. Use `pip install cogency[anthropic]`")

from cogency.llm.base import BaseLLM
from cogency.resilience import safe


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
        super().__init__("anthropic", api_keys)
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

        self._client = anthropic.AsyncAnthropic(api_key="placeholder")

    def _get_client(self):
        """Get client instance with current API key."""
        # Update the API key on the existing client
        self._client.api_key = self.get_api_key()
        return self._client


    @safe()
    async def run(self, messages: List[Dict[str, str]], **kwargs) -> str:
        client = self._get_client()
        anthropic_messages = self._convert_msgs(messages)

        res = await client.messages.create(
            model=self.model,
            messages=anthropic_messages,
            **self.kwargs,
            **kwargs,
        )
        return res.content[0].text

    @safe()
    async def stream(self, messages: List[Dict[str, str]], yield_interval: float = 0.0, **kwargs) -> AsyncIterator[str]:
        client = self._get_client()
        anthropic_messages = self._convert_msgs(messages)

        async with client.messages.stream(
            model=self.model,
            messages=anthropic_messages,
            **self.kwargs,
            **kwargs,
        ) as stream:
            async for text in stream.text_stream:
                yield text
