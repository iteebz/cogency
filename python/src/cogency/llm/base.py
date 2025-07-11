from abc import ABC, abstractmethod
from typing import Dict, List


class BaseLLM(ABC):
    """Base class for all LLM implementations in the cogency framework."""

    def __init__(self, api_key: str = None, key_rotator=None, **kwargs):
        self.api_key = api_key
        self.key_rotator = key_rotator

    @abstractmethod
    def invoke(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Generate a response from the LLM given a list of messages.

        Args:
            messages: List of message dictionaries with 'role' and 'content' keys
            **kwargs: Additional parameters for the LLM call

        Returns:
            String response from the LLM
        """
        pass
