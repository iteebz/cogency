import os
from typing import AsyncIterator, Dict, List, Optional, Union

try:
    import google.generativeai as genai
except ImportError:
    raise ImportError("Google Gemini support not installed. Use `pip install cogency[gemini]`")

from cogency.llm.base import BaseLLM
from cogency.utils.keys import KeyManager
from cogency.errors import ConfigurationError
from cogency.resilience import safe


class GeminiLLM(BaseLLM):
    def __init__(
        self,
        api_keys: Union[str, List[str]] = None,
        model: str = "gemini-2.0-flash",
        timeout: float = 15.0,
        temperature: float = 0.7,
        max_retries: int = 3,
        **kwargs,
    ):
        # Beautiful unified key management - auto-detects, handles all scenarios
        self.keys = KeyManager.for_provider("gemini", api_keys)
        super().__init__(self.keys.api_key, self.keys.key_rotator)
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
        current_key = self.keys.get_current()

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

    def _get_client(self):
        """Get model instance."""
        return self._current_model

    def _init_client(self):
        """Alias for _init_current_model to match mixin interface."""
        self._init_current_model()

    def _rotate_client(self):
        """Rotate to the next key and re-initialize the client."""
        if self.keys.has_multiple():
            self._init_client()

    @safe()
    async def invoke(self, messages: List[Dict[str, str]], **kwargs) -> str:
        # Convert messages to Gemini format (simple text concatenation for now)
        # Gemini's chat format is different - it expects conversation history
        prompt = "".join([f"{msg['role']}: {msg['content']}" for msg in messages])

        try:
            res = await self._current_model.generate_content_async(prompt, **kwargs)
            
            # Handle different response formats from Gemini API
            if hasattr(res, 'text') and res.text:
                return res.text
            elif hasattr(res, 'candidates') and res.candidates:
                # Try to get text from first candidate
                candidate = res.candidates[0]
                if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                    if candidate.content.parts and hasattr(candidate.content.parts[0], 'text'):
                        return candidate.content.parts[0].text
            
            # Fallback: convert to string
            return str(res)
            
        except Exception as e:
            error_str = str(e).lower()
            # Handle rate limiting and invalid API keys gracefully - try rotating key
            if any(keyword in error_str for keyword in ["429", "quota", "api key not valid", "invalid api key", "api_key_invalid"]):
                rotation_msg = self.handle_rate_limit(e)
                if self.key_rotator:
                    self._rotate_client()
                    # Retry with next key for invalid API key errors
                    if "api key" in error_str or "api_key_invalid" in error_str:
                        return await self.invoke(messages, **kwargs)
            raise

    @safe()
    async def stream(self, messages: List[Dict[str, str]], yield_interval: float = 0.0, **kwargs) -> AsyncIterator[str]:
        self._rotate_client()

        # Convert messages to Gemini format (simple text concatenation for now)
        prompt = "".join([f"{msg['role']}: {msg['content']}" for msg in messages])

        try:
            response = await self._current_model.generate_content_async(
                prompt, stream=True, **kwargs
            )
            
            async for chunk in response:
                if chunk.text:
                    yield chunk.text
        except Exception as e:
            error_str = str(e).lower()
            # Handle rate limiting and invalid API keys gracefully
            if any(keyword in error_str for keyword in ["429", "quota", "api key not valid", "invalid api key", "api_key_invalid"]):
                rotation_msg = self.handle_rate_limit(e)
                if self.key_rotator:
                    self._rotate_client()
                    # Retry with next key for invalid API key errors
                    if "api key" in error_str or "api_key_invalid" in error_str:
                        async for chunk in self.stream(messages, yield_interval, **kwargs):
                            yield chunk
                        return
            raise