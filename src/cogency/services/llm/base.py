import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Union

from cogency.resilience import safe
from cogency.types.cache import cached_llm_call
from cogency.utils.keys import KeyManager
from cogency.utils.results import Result

logger = logging.getLogger(__name__)


class BaseLLM(ABC):
    """
    Base class for all LLM implementations in the cogency framework.

    All LLM providers support:
    - Streaming execution for real-time output
    - Automatic key rotation for high-volume usage
    - Rate limiting via yield_interval parameter
    - Unified interface across providers
    - Dynamic model/parameter configuration
    """

    def __init__(
        self,
        provider_name: str,
        api_keys: Union[str, List[str]] = None,
        enable_cache: bool = True,
        **kwargs,
    ):
        # Automatic key management - handles single/multiple keys, rotation, env detection
        self.keys = KeyManager.for_provider(provider_name, api_keys)
        self.provider_name = provider_name
        self.enable_cache = enable_cache

    def next_key(self) -> str:
        """Get next API key - rotates automatically on every call."""
        return self.keys.get_next()

    @safe.network()
    async def run(self, messages: List[Dict[str, str]], **kwargs) -> Result:
        """Generate a response from the LLM given a list of messages.

        Args:
            messages: List of message dictionaries with 'role' and 'content' keys
            **kwargs: Additional parameters for the LLM call

        Returns:
            Result containing string response from the LLM or error
        """
        return await cached_llm_call(
            self._run_impl, messages, use_cache=self.enable_cache, **kwargs
        )

    @abstractmethod
    async def _run_impl(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Internal implementation of LLM call - to be implemented by subclasses."""
        pass

    def _format(self, msgs: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Convert to provider format (standard role/content structure)."""
        return [{"role": m["role"], "content": m["content"]} for m in msgs]

    @safe.network()
    @abstractmethod
    async def stream(self, messages: List[Dict[str, str]], **kwargs) -> Result:
        """Generate a streaming response from the LLM given a list of messages.

        Args:
            messages: List of message dictionaries with 'role' and 'content' keys
            yield_interval: Minimum time between yields for rate limiting (seconds)
            **kwargs: Additional parameters for the LLM call

        Returns:
            Result containing AsyncIterator[str] for streaming response or error
        """
        pass
