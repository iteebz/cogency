"""OpenRouter provider - cost-effective model routing with OpenAI compatibility."""

import openai
from resilient_result import Ok, Result

from .base import Provider, rotate_retry, setup_rotator
from .utils.tokens import count


class OpenRouter(Provider):
    def __init__(
        self,
        api_keys=None,
        llm_model: str = "anthropic/claude-3.5-haiku",
        temperature: float = 0.7,
        max_tokens: int = 16384,
        top_p: float = 1.0,
        frequency_penalty: float = 0.0,
        presence_penalty: float = 0.0,
        **kwargs,
    ):
        rotator = setup_rotator("openrouter", api_keys, required=True)

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
            base_url="https://openrouter.ai/api/v1",
            timeout=self.timeout,
            max_retries=self.max_retries,
        )

    @rotate_retry
    async def generate(self, messages: list[dict[str, str]], **kwargs) -> Result:
        """Generate LLM response with metrics and caching."""
        count(messages, self.model)

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

        count([{"role": "assistant", "content": response}], self.model)
        # Cache the response
        if self._cache:
            await self._cache.set(messages, response, **kwargs)

        return Ok(response)
