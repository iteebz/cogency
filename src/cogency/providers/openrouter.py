"""OpenRouter provider - cost-effective model routing with OpenAI compatibility."""

from typing import AsyncIterator, Dict, List

import openai
from resilient_result import Ok, Result

from cogency.events import emit
from cogency.observe.tokens import cost, count

from .base import Provider


class OpenRouter(Provider):
    def __init__(
        self,
        llm_model: str = "anthropic/claude-3.5-haiku",
        temperature: float = 0.7,
        max_tokens: int = 16384,
        top_p: float = 1.0,
        frequency_penalty: float = 0.0,
        presence_penalty: float = 0.0,
        **kwargs,
    ):
        # Universal params to base class
        super().__init__(model=llm_model, temperature=temperature, max_tokens=max_tokens, **kwargs)
        # Provider-specific params
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

    async def run(self, messages: List[Dict[str, str]], **kwargs) -> Result:
        """Generate LLM response with metrics and caching."""
        tin = count(messages, self.model)

        # Check cache first
        if self._cache:
            cached_response = await self._cache.get(messages, **kwargs)
            if cached_response:
                return Ok(cached_response)

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
        response = res.choices[0].message.content

        tout = count([{"role": "assistant", "content": response}], self.model)
        emit(
            "provider",
            provider=self.provider_name,
            model=self.model,
            tin=tin,
            tout=tout,
            cost=cost(tin, tout, self.model),
        )

        # Cache response
        if self._cache:
            await self._cache.set(messages, response, cache_type="llm", **kwargs)

        return Ok(response)

    async def stream(self, messages: List[Dict[str, str]], **kwargs) -> AsyncIterator[str]:
        """Generate streaming LLM response."""
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
