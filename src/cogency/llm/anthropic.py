from typing import AsyncIterator, Dict, List, Union

try:
    import anthropic
except ImportError:
    raise ImportError(
        "Anthropic support not installed. Use `pip install cogency[anthropic]`"
    ) from None

from cogency.constants import MAX_TOKENS
from cogency.llm.base import BaseLLM
from cogency.resilience import safe


class AnthropicLLM(BaseLLM):
    def __init__(
        self,
        api_keys: Union[str, List[str]] = None,
        model: str = "claude-3-5-sonnet-20241022",
        timeout: float = 15.0,
        temperature: float = 0.7,
        max_tokens: int = MAX_TOKENS,
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
        self._client.api_key = self.next_key()
        return self._client

    @safe.llm()
    async def _run_impl(self, messages: List[Dict[str, str]], **kwargs) -> str:
        client = self._get_client()
        anthropic_messages = self._format(messages)

        res = await client.messages.create(
            model=self.model,
            messages=anthropic_messages,
            **self.kwargs,
            **kwargs,
        )
        return res.content[0].text

    @safe.llm()
    async def stream(self, messages: List[Dict[str, str]], **kwargs) -> AsyncIterator[str]:
        client = self._get_client()
        anthropic_messages = self._format(messages)

        async with client.messages.stream(
            model=self.model,
            messages=anthropic_messages,
            **self.kwargs,
            **kwargs,
        ) as stream:
            async for text in stream.text_stream:
                yield text
