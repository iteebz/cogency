from typing import AsyncIterator, Dict, List, Union

try:
    import openai
except ImportError:
    raise ImportError("OpenAI support not installed. Use `pip install cogency[openai]`") from None

from cogency.constants import MAX_TOKENS
from cogency.llm.base import BaseLLM
from cogency.resilience import safe


class OpenAILLM(BaseLLM):
    def __init__(
        self,
        api_keys: Union[str, List[str]] = None,
        model: str = "gpt-4o",
        timeout: float = 15.0,
        temperature: float = 0.7,
        max_retries: int = 3,
        max_tokens: int = MAX_TOKENS,
        **kwargs,
    ):
        super().__init__("openai", api_keys)
        self.model = model

        # Configuration parameters
        self.timeout = timeout
        self.temperature = temperature
        self.max_retries = max_retries

        # Build kwargs for OpenAI chat completions (filtering client-level params)
        self.kwargs = {
            "temperature": temperature,
            "max_tokens": max_tokens,
            **kwargs,
        }
        self.client_kwargs = {
            "timeout": timeout,
            "max_retries": max_retries,
        }

        self._client = openai.AsyncOpenAI(api_key="placeholder", **self.client_kwargs)

    def _get_client(self):
        """Get client instance with current API key."""
        # Update the API key on the existing client
        self._client.api_key = self.next_key()
        return self._client

    @safe()
    async def _run_impl(self, messages: List[Dict[str, str]], **kwargs) -> str:
        client = self._get_client()
        msgs = self._format(messages)
        res = await client.chat.completions.create(
            model=self.model,
            messages=msgs,
            **self.kwargs,
            **kwargs,
        )
        return res.choices[0].message.content

    @safe()
    async def stream(self, messages: List[Dict[str, str]], **kwargs) -> AsyncIterator[str]:
        client = self._get_client()
        msgs = self._format(messages)
        stream = await client.chat.completions.create(
            model=self.model,
            messages=msgs,
            stream=True,
            **self.kwargs,
            **kwargs,
        )
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
