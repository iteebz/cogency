"""Ollama provider - local LLM and embedding with OpenAI-compatible API."""

import openai
from resilient_result import Ok, Result

from .base import Provider, rotate_retry, setup_rotator
from .utils.tokens import count


class Ollama(Provider):
    def __init__(
        self,
        api_key: str = None,
        llm_model: str = "llama3.1:8b",
        embed_model: str = "nomic-embed-text",
        dimensionality: int = 768,
        temperature: float = 0.7,
        max_tokens: int = 16384,
        timeout: float = 60.0,  # Local models need more time
        base_url: str = "http://localhost:11434/v1",
        **kwargs,
    ):
        rotator = setup_rotator("ollama", api_key, required=False)

        super().__init__(
            rotator=rotator,
            model=llm_model,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=timeout,
            **kwargs,
        )
        # Ollama-specific params
        self.embed_model = embed_model
        self.dimensionality = dimensionality
        self.base_url = base_url

    def _get_client(self):
        return openai.AsyncOpenAI(
            base_url=self.base_url,
            api_key="ollama",  # Ollama doesn't need real API key
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
            **kwargs,
        )
        response = res.choices[0].message.content

        count([{"role": "assistant", "content": response}], self.model)
        # Cache the response
        if self._cache:
            await self._cache.set(messages, response, **kwargs)

        return Ok(response)
