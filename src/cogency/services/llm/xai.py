from typing import AsyncIterator, Dict, List, Union

try:
    import openai
except ImportError:
    raise ImportError(
        "OpenAI support not installed (required for xAI OpenAI-compatible API). "
        "Use `pip install cogency[openai]`"
    ) from None

from cogency.services.llm.base import BaseLLM


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
        super().__init__("xai", api_keys)
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

    def _get_client(self):
        """Get client instance with current API key."""
        key = self.next_key()
        return openai.AsyncOpenAI(api_key=key, base_url="https://api.x.ai/v1", **self.client_kwargs)

    async def _run_impl(self, messages: List[Dict[str, str]], **kwargs) -> str:
        client = self._get_client()
        xai_messages = self._format(messages)

        res = await client.chat.completions.create(
            model=self.model,
            messages=xai_messages,
            **self.kwargs,
            **kwargs,
        )
        return res.choices[0].message.content

    async def stream(self, messages: List[Dict[str, str]], **kwargs) -> AsyncIterator[str]:
        client = self._get_client()
        xai_messages = self._format(messages)

        try:
            stream = await client.chat.completions.create(
                model=self.model,
                messages=xai_messages,
                stream=True,
                **self.kwargs,
                **kwargs,
            )

            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            raise e
