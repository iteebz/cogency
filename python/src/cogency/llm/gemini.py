from typing import Dict, List, Optional

from langchain_core.language_models import BaseChatModel
from langchain_google_genai import ChatGoogleGenerativeAI

from cogency.llm.base import BaseLLM


class GeminiLLM(BaseLLM):
    def __init__(
        self,
        api_key: str = None,
        key_rotator=None,
        model: str = "gemini-2.5-flash",
        **kwargs,
    ):
        super().__init__(api_key, key_rotator)
        self.model = model
        # Set more reasonable timeout for faster failures
        if "timeout" not in kwargs:
            kwargs["timeout"] = 15.0  # 15 second timeout instead of default 60+
        self.kwargs = kwargs
        self._llm_instances: Dict[str, BaseChatModel] = {}  # Cache for LLM instances
        self._current_llm: Optional[BaseChatModel] = None  # Currently active LLM instance
        self._init_current_llm()  # Initialize the first LLM instance

    def _init_current_llm(self):
        """Initializes or retrieves the current LLM instance based on the active key."""
        current_key = self.key_rotator.get_key() if self.key_rotator else self.api_key

        if not current_key:
            raise ValueError("API key must be provided either directly or via KeyRotator.")

        if current_key not in self._llm_instances:
            self._llm_instances[current_key] = ChatGoogleGenerativeAI(
                model=self.model, google_api_key=current_key, **self.kwargs
            )

        self._current_llm = self._llm_instances[current_key]

    def invoke(self, messages: List[Dict[str, str]], **kwargs) -> str:
        # Rotate key and update current LLM if a rotator is used
        if self.key_rotator:
            self._init_current_llm()

        if not self._current_llm:
            raise RuntimeError("LLM instance not initialized.")

        res = self._current_llm.invoke(messages, **kwargs)
        return res.content
