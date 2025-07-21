import asyncio
import logging
from abc import ABC, abstractmethod
from typing import AsyncIterator, Dict, List, Any

logger = logging.getLogger(__name__)


class BaseLLM(ABC):
    """
    Base class for all LLM implementations in the cogency framework.
    
    All LLM providers support:
    - Streaming execution for real-time output
    - Key rotation for high-volume usage  
    - Rate limiting via yield_interval parameter
    - Unified interface across providers
    - Dynamic model/parameter configuration
    """

    def __init__(self, api_key: str = None, key_rotator=None, **kwargs):
        self.api_key = api_key
        self.key_rotator = key_rotator

    def handle_rate_limit(self, error: Exception) -> str:
        """Handle rate limit by rotating key if available."""
        if self.key_rotator:
            return self.key_rotator.rotate_key()
        else:
            current_key = self.api_key
            key_suffix = current_key[-8:] if current_key else "unknown"
            return f"Key *{key_suffix} rate limited (no rotation available)"

    @abstractmethod
    async def invoke(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Generate a response from the LLM given a list of messages.

        Args:
            messages: List of message dictionaries with 'role' and 'content' keys
            **kwargs: Additional parameters for the LLM call

        Returns:
            String response from the LLM
        """
        pass

    async def ainvoke(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """LangGraph compatibility method - wrapper around invoke()."""
        return await self.invoke(messages, **kwargs)

    def _convert_msgs(self, msgs: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Convert to provider format (standard role/content structure)."""
        return [{"role": m["role"], "content": m["content"]} for m in msgs]

    def _ensure_current_key(self) -> str:
        """Validate and return current API key, raising ConfigurationError if missing."""
        from cogency.errors import ConfigurationError
        current_key = self.keys.get_current()
        if not current_key:
            raise ConfigurationError(
                "API key must be provided either directly or via KeyRotator.",
                error_code="NO_CURRENT_API_KEY",
            )
        return current_key

    @abstractmethod
    async def stream(self, messages: List[Dict[str, str]], yield_interval: float = 0.0, **kwargs) -> AsyncIterator[str]:
        """Generate a streaming response from the LLM given a list of messages.

        Args:
            messages: List of message dictionaries with 'role' and 'content' keys
            yield_interval: Minimum time between yields for rate limiting (seconds)
            **kwargs: Additional parameters for the LLM call

        Yields:
            String chunks from the LLM response
        """
        pass


