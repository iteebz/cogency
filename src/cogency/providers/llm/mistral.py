"""Mistral AI provider - streaming chat with tool calling and key rotation."""

from typing import AsyncIterator, Dict, List

from mistralai import Mistral as MistralClient

from cogency.providers.llm.base import LLM


class Mistral(LLM):
    def __init__(
        self,
        model: str = "mistral-small-latest",
        temperature: float = 0.7,
        max_tokens: int = 16384,
        top_p: float = 1.0,
        **kwargs,
    ):
        # Universal params to base class
        super().__init__(model=model, temperature=temperature, max_tokens=max_tokens, **kwargs)
        # Mistral-specific params
        self.top_p = top_p

    def _get_client(self):
        return MistralClient(api_key=self.next_key())

    async def _run_impl(self, messages: List[Dict[str, str]], **kwargs) -> str:
        client = self._get_client()
        res = await client.chat.complete_async(
            model=self.model,
            messages=self._format(messages),
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            top_p=self.top_p,
            **kwargs,
        )
        return res.choices[0].message.content

    async def _stream_impl(self, messages: List[Dict[str, str]], **kwargs) -> AsyncIterator[str]:
        client = self._get_client()
        try:
            stream = await client.chat.stream_async(
                model=self.model,
                messages=self._format(messages),
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                top_p=self.top_p,
                **kwargs,
            )
            async for chunk in stream:
                if chunk.data.choices[0].delta.content:
                    yield chunk.data.choices[0].delta.content
        except Exception as e:
            raise e
