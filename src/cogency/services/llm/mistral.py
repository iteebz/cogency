from typing import AsyncIterator, Dict, List

try:
    from mistralai import Mistral
except ImportError:
    raise ImportError("Mistral support not installed. Use `pip install cogency[mistral]`") from None

from cogency.services.llm.base import BaseLLM


class MistralLLM(BaseLLM):
    def __init__(self, **kwargs):
        super().__init__("mistral", **kwargs)
    
    @property
    def default_model(self) -> str:
        return "mistral-large-latest"

    def _get_client(self):
        return Mistral(api_key=self.next_key())

    async def _run_impl(self, messages: List[Dict[str, str]], **kwargs) -> str:
        client = self._get_client()
        res = await client.chat.complete_async(
            model=self.model,
            messages=self._format(messages),
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            **kwargs,
        )
        return res.choices[0].message.content

    async def stream(self, messages: List[Dict[str, str]], **kwargs) -> AsyncIterator[str]:
        client = self._get_client()
        try:
            stream = await client.chat.stream_async(
                model=self.model,
                messages=self._format(messages),
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                **kwargs,
            )
            async for chunk in stream:
                if chunk.data.choices[0].delta.content:
                    yield chunk.data.choices[0].delta.content
        except Exception as e:
            raise e
