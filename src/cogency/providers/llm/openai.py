"""OpenAI GPT provider - streaming chat with tool calling and key rotation."""

from typing import AsyncIterator, Dict, List

import openai

from cogency.providers.llm.base import LLM


class OpenAI(LLM):
    def __init__(self, **kwargs):
        super().__init__("openai", **kwargs)

    @property
    def default_model(self) -> str:
        return "gpt-4o-mini"  # Fast, cost-aware default

    def _get_client(self):
        return openai.AsyncOpenAI(
            api_key=self.next_key(),
            timeout=self.timeout,
            max_retries=self.max_retries,
        )

    async def _run_impl(self, messages: List[Dict[str, str]], **kwargs) -> str:
        client = self._get_client()
        res = await client.chat.completions.create(
            model=self.model,
            messages=self._format(messages),
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            **kwargs,
        )
        return res.choices[0].message.content

    async def _stream_impl(self, messages: List[Dict[str, str]], **kwargs) -> AsyncIterator[str]:
        client = self._get_client()
        stream = await client.chat.completions.create(
            model=self.model,
            messages=self._format(messages),
            stream=True,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            **kwargs,
        )
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
