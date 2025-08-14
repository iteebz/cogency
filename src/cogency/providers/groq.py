"""Groq provider - ultra-fast hardware inference with OpenAI compatibility."""

from collections.abc import AsyncIterator

import openai
from resilient_result import Ok, Result


try:
    from .tokens import cost, count

    from .base import Provider, rotate_retry, setup_rotator
except ImportError:
    from tokens import cost, count
    from base import Provider, rotate_retry, setup_rotator


class Groq(Provider):
    def __init__(
        self,
        api_keys=None,
        llm_model: str = "llama-3.3-70b-versatile",
        temperature: float = 0.7,
        max_tokens: int = 16384,
        top_p: float = 1.0,
        frequency_penalty: float = 0.0,
        presence_penalty: float = 0.0,
        **kwargs,
    ):
        rotator = setup_rotator("groq", api_keys, required=True)

        super().__init__(
            rotator=rotator,
            model=llm_model,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )
        # Provider-specific params
        self.top_p = top_p
        self.frequency_penalty = frequency_penalty
        self.presence_penalty = presence_penalty

    def _get_client(self):
        return openai.AsyncOpenAI(
            api_key=self.next_key(),
            base_url="https://api.groq.com/openai/v1",
            timeout=self.timeout,
            max_retries=self.max_retries,
        )

    @rotate_retry
    async def generate(self, messages: list[dict[str, str]], **kwargs) -> Result:
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
