from abc import ABC, abstractmethod
from typing import AsyncIterator, Dict, List


class BaseLLM(ABC):
    """
    Base class for all LLM implementations in the cogency framework.
    
    All LLM providers support:
    - Streaming execution for real-time output
    - Key rotation for high-volume usage  
    - Rate limiting via yield_interval parameter
    - Unified interface across providers
    """

    def __init__(self, api_key: str = None, key_rotator=None, **kwargs):
        self.api_key = api_key
        self.key_rotator = key_rotator

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
