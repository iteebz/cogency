"""Anthropic Claude provider - streaming chat with tool calling and key rotation."""

import logging
from typing import AsyncIterator, Dict, List

import anthropic

from cogency.providers.llm.base import LLM

logger = logging.getLogger(__name__)


class Anthropic(LLM):
    def __init__(self, **kwargs):
        super().__init__("anthropic", **kwargs)

    @property
    def default_model(self) -> str:
        return "claude-3-5-haiku-20241022"  # Fast, cost-aware default

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
                **kwargs,
            ) as stream:
                async for text in stream.text_stream:
                    yield text
        except Exception as e:
            logger.error(f"Anthropic streaming failed: {e}")
            return
