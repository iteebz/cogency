"""OpenRouter LLM provider - cost-effective model routing with OpenAI compatibility."""

from typing import AsyncIterator, Dict, List

import openai

from cogency.providers.llm.base import LLM


class OpenRouter(LLM):
    def __init__(
        self,
        model: str = "anthropic/claude-3.5-haiku",
        temperature: float = 0.7,
        max_tokens: int = 16384,
        top_p: float = 1.0,
        frequency_penalty: float = 0.0,
        presence_penalty: float = 0.0,
        **kwargs,
    ):
        # Universal params to base class
        super().__init__(model=model, temperature=temperature, max_tokens=max_tokens, **kwargs)
        # Provider-specific params handled locally
        self.top_p = top_p
        self.frequency_penalty = frequency_penalty
        self.presence_penalty = presence_penalty

    def _get_client(self):
        return openai.AsyncOpenAI(
            api_key=self.next_key(),
            base_url="https://openrouter.ai/api/v1",
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
            top_p=self.top_p,
            frequency_penalty=self.frequency_penalty,
            presence_penalty=self.presence_penalty,
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
            top_p=self.top_p,
            frequency_penalty=self.frequency_penalty,
            presence_penalty=self.presence_penalty,
            **kwargs,
        )
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
