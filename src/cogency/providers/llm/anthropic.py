"""Anthropic Claude provider - streaming chat with tool calling and key rotation."""

import logging
from typing import AsyncIterator, Dict, List

import anthropic

from cogency.providers.llm.base import LLM

logger = logging.getLogger(__name__)


class Anthropic(LLM):
    def __init__(
        self,
        model: str = "claude-3-5-haiku-20241022",
        temperature: float = 0.7,
        max_tokens: int = 16384,
        top_k: int = 40,
        top_p: float = 1.0,
        **kwargs,
    ):
        # Universal params to base class
        super().__init__(model=model, temperature=temperature, max_tokens=max_tokens, **kwargs)
        # Anthropic-specific params
        self.top_k = top_k
        self.top_p = top_p

    def _get_client(self):
        return anthropic.AsyncAnthropic(
            api_key=self.next_key(),
            timeout=self.timeout,
            max_retries=self.max_retries,
        )

    async def _run_impl(self, messages: List[Dict[str, str]], **kwargs) -> str:
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
        return res.content[0].text

    async def _stream_impl(self, messages: List[Dict[str, str]], **kwargs) -> AsyncIterator[str]:
        client = self._get_client()
        try:
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
        except Exception as e:
            logger.error(f"Anthropic streaming failed: {e}")
            raise e
