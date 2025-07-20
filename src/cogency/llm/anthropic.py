from typing import AsyncIterator, Dict, List, Optional, Union

try:
    import anthropic
except ImportError:
    raise ImportError("Anthropic support not installed. Use `pip install cogency[anthropic]`")

from cogency.llm.base import BaseLLM
from cogency.utils.keys import KeyManager
from cogency.errors import ConfigurationError


class AnthropicLLM(BaseLLM):
    def __init__(
        self,
        api_keys: Union[str, List[str]] = None,
        model: str = "claude-3-5-sonnet-20241022",
        timeout: float = 15.0,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        max_retries: int = 3,
        **kwargs,
    ):
        # Beautiful unified key management - auto-detects, handles all scenarios
        self.keys = KeyManager.for_provider("anthropic", api_keys)
        super().__init__(self.keys.api_key, self.keys.key_rotator)
        self.model = model

        # Configuration parameters
        self.timeout = timeout
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.max_retries = max_retries

        # Build kwargs for Anthropic client
        self.kwargs = {
            "timeout": timeout,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "max_retries": max_retries,
            **kwargs,
        }

        self._client: Optional[anthropic.AsyncAnthropic] = None
        self._init_client()  # Initialize the client

    def _init_client(self):
        """Initializes the Anthropic client based on the active key."""
        current_key = self.keys.get_current()

        if not current_key:
            raise ConfigurationError(
                "API key must be provided either directly or via KeyRotator.",
                error_code="NO_CURRENT_API_KEY",
            )

        self._client = anthropic.AsyncAnthropic(api_key=current_key)

    def _get_client(self):
        """Get client instance."""
        return self._client

    def _rotate_client(self):
        """Rotate to the next key and re-initialize the client."""
        if self.keys.has_multiple():
            self._init_client()

    def _convert_msgs(self, msgs: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Convert to provider format."""
        return [{"role": m["role"], "content": m["content"]} for m in msgs]

    async def invoke(self, messages: List[Dict[str, str]], **kwargs) -> str:
        self._rotate_client()
        anthropic_messages = self._convert_msgs(messages)

        res = await self._client.messages.create(
            model=self.model,
            messages=anthropic_messages,
            **self.kwargs,
            **kwargs,
        )
        return res.content[0].text

    async def stream(self, messages: List[Dict[str, str]], yield_interval: float = 0.0, **kwargs) -> AsyncIterator[str]:
        self._rotate_client()
        anthropic_messages = self._convert_msgs(messages)

        async with self._client.messages.stream(
            model=self.model,
            messages=anthropic_messages,
            **self.kwargs,
            **kwargs,
        ) as stream:
            async for text in stream.text_stream:
                yield text
