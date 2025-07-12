from typing import AsyncIterator, Dict, List, Optional, Union

import google.generativeai as genai

from cogency.llm.base import BaseLLM
from cogency.llm.key_rotator import KeyRotator
from cogency.utils.interrupt import interruptable
from cogency.utils.errors import ConfigurationError


class GeminiLLM(BaseLLM):
    def __init__(
        self,
        api_keys: Union[str, List[str]] = None,
        model: str = "gemini-2.5-flash",
        timeout: float = 15.0,
        temperature: float = 0.7,
        max_retries: int = 3,
        **kwargs,
    ):
        # Validate inputs
        if not api_keys:
            raise ConfigurationError("API keys must be provided", error_code="NO_API_KEYS")

        # Handle the cleaner interface: if list provided, create key rotator internally
        if isinstance(api_keys, list) and len(api_keys) > 1:
            key_rotator = KeyRotator(api_keys)
            api_key = None
        elif isinstance(api_keys, list) and len(api_keys) == 1:
            key_rotator = None
            api_key = api_keys[0]
        else:
            key_rotator = None
            api_key = api_keys

        super().__init__(api_key, key_rotator)
        self.model = model

        # Configuration parameters
        self.timeout = timeout
        self.temperature = temperature
        self.max_retries = max_retries

        # Build kwargs for Gemini client
        self.kwargs = {
            "timeout": timeout,
            "temperature": temperature,
            "max_retries": max_retries,
            **kwargs,
        }

        self._model_instances: Dict[str, genai.GenerativeModel] = {}  # Cache for model instances
        self._current_model: Optional[genai.GenerativeModel] = None  # Currently active model instance
        self._init_current_model()  # Initialize the first model instance

    def _init_current_model(self):
        """Initializes or retrieves the current model instance based on the active key."""
        current_key = self.key_rotator.get_key() if self.key_rotator else self.api_key

        if not current_key:
            raise ConfigurationError(
                "API key must be provided either directly or via KeyRotator.",
                error_code="NO_CURRENT_API_KEY",
            )

        if current_key not in self._model_instances:
            genai.configure(api_key=current_key)
            # Only pass GenerationConfig-compatible parameters
            generation_params = {
                "temperature": self.temperature,
                # Add other valid GenerationConfig params as needed
            }
            # Filter out non-GenerationConfig params like timeout, max_retries
            for k, v in self.kwargs.items():
                if k in ["temperature", "max_output_tokens", "top_p", "top_k", "candidate_count", "stop_sequences"]:
                    generation_params[k] = v
            
            self._model_instances[current_key] = genai.GenerativeModel(
                model_name=self.model,
                generation_config=genai.types.GenerationConfig(**generation_params)
            )

        self._current_model = self._model_instances[current_key]

    @interruptable
    async def invoke(self, messages: List[Dict[str, str]], **kwargs) -> str:
        # Rotate key and update current model if a rotator is used
        if self.key_rotator:
            self._init_current_model()

        if not self._current_model:
            raise RuntimeError("Gemini model not initialized.")

        # Convert messages to Gemini format (simple text concatenation for now)
        # Gemini's chat format is different - it expects conversation history
        prompt = "\n".join([f"{msg['role']}: {msg['content']}" for msg in messages])

        res = await self._current_model.generate_content_async(prompt, **kwargs)
        return res.text

    async def stream(self, messages: List[Dict[str, str]], yield_interval: float = 0.0, **kwargs) -> AsyncIterator[str]:
        # Rotate key and update current model if a rotator is used
        if self.key_rotator:
            self._init_current_model()

        if not self._current_model:
            raise RuntimeError("Gemini model not initialized.")

        # Convert messages to Gemini format (simple text concatenation for now)
        prompt = "\n".join([f"{msg['role']}: {msg['content']}" for msg in messages])

        response = await self._current_model.generate_content_async(
            prompt, stream=True, **kwargs
        )
        
        async for chunk in response:
            if chunk.text:
                yield chunk.text
