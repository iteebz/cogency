from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.language_models import BaseChatModel
import itertools

class KeyRotator:
    """Simple key rotator for API rate limit avoidance."""
    def __init__(self, keys: List[str]):
        self.keys = keys
        self.cycle = itertools.cycle(keys)
    
    def get_key(self) -> str:
        """Get next key in rotation."""
        return next(self.cycle)

class LLM(ABC):
    def __init__(self, api_key: str = None, key_rotator: KeyRotator = None, **kwargs):
        self.api_key = api_key
        self.key_rotator = key_rotator

    @abstractmethod
    def invoke(self, messages: list[dict[str, str]], **kwargs) -> str:
        pass

class GeminiLLM(LLM):
    def __init__(self, api_key: str = None, key_rotator: KeyRotator = None, model: str = "gemini-2.5-flash", **kwargs):
        super().__init__(api_key, key_rotator)
        self.model = model
        self.kwargs = kwargs
        self.llm: BaseChatModel = None
        self._init_llm()

    def _init_llm(self):
        """Initialize LLM with current key."""
        current_key = self.key_rotator.get_key() if self.key_rotator else self.api_key
        self.llm = ChatGoogleGenerativeAI(model=self.model, google_api_key=current_key, **self.kwargs)

    def invoke(self, messages: list[dict[str, str]], **kwargs) -> str:
        # Rotate key on each invoke to spread load
        if self.key_rotator:
            self._init_llm()
        res = self.llm.invoke(messages, **kwargs)
        return res.content


