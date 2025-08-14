"""Anthropic Claude provider - streaming chat with tool calling and key rotation."""

from collections.abc import AsyncIterator
from typing import Union

import anthropic
from resilient_result import Ok, Result

from .base import Provider, rotate_retry, setup_rotator
from .utils.tokens import cost, count


class Anthropic(Provider):
    def __init__(
        self,
        api_keys: Union[str, list[str]] = None,
        llm_model: str = "claude-3-5-haiku-20241022",
        temperature: float = 0.7,
        max_tokens: int = 16384,
        top_k: int = 40,
        top_p: float = 1.0,
        **kwargs,
    ):
        rotator = setup_rotator("anthropic", api_keys, required=True)

        super().__init__(
            rotator=rotator,
            model=llm_model,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )
        # Anthropic-specific params
        self.top_k = top_k
        self.top_p = top_p

    def _get_client(self):
        return anthropic.AsyncAnthropic(
            api_key=self.next_key(),
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
                return Ok(
                    {
                        "content": cached_response,
                        "tokens": {
                            "input": tin,
                            "output": 0,  # Cached, no output tokens charged
                            "cost": 0.0,
                        },
                    }
                )

        client = self._get_client()
        res = await client.messages.create(
            model=self.model,
            messages=self._format(messages),
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            top_k=self.top_k,
            top_p=self.top_p,
            **kwargs,
        )
        response = res.content[0].text
        tout = count([{"role": "assistant", "content": response}], self.model)

        # Cache response
        if self._cache:
            await self._cache.set(messages, response, cache_type="llm", **kwargs)

        return Ok(
            {
                "content": response,
                "tokens": {"input": tin, "output": tout, "cost": cost(tin, tout, self.model)},
            }
        )

    async def stream(self, messages: list[dict[str, str]], **kwargs) -> AsyncIterator[str]:
        """Generate streaming LLM response."""
        client = self._get_client()
        async with client.messages.stream(
            model=self.model,
            messages=self._format(messages),
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            top_k=self.top_k,
            top_p=self.top_p,
            **kwargs,
        ) as stream:
            async for text in stream.text_stream:
                yield text
