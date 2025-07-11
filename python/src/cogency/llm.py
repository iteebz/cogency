from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.language_models import BaseChatModel

class LLM(ABC):
    def __init__(self, api_key: str, **kwargs):
        self.api_key = api_key

    @abstractmethod
    def invoke(self, prompt: str, **kwargs) -> str:
        pass

class GeminiLLM(LLM):
    def __init__(self, api_key: str, model: str = "gemini-2.5-flash", **kwargs):
        super().__init__(api_key)
        self.llm: BaseChatModel = ChatGoogleGenerativeAI(model=model, google_api_key=api_key, **kwargs)

    def invoke(self, prompt: str, **kwargs) -> str:
        res = self.llm.invoke(prompt, **kwargs)
        return res.content


