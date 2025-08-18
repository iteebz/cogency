"""Anthropic provider - LLM protocol implementation."""

from ...core.protocols import LLM
from ..result import Err, Ok, Result


class Anthropic(LLM):
    """Anthropic provider implementing LLM protocol."""

    def __init__(
        self,
        api_key: str,
        llm_model: str = "claude-3-5-sonnet-20241022",
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ):
        self.api_key = api_key
        self.llm_model = llm_model
        self.temperature = temperature
        self.max_tokens = max_tokens

    async def generate(self, messages: list[dict]) -> Result[str, str]:
        """Generate text from conversation messages."""
        try:
            import anthropic

            client = anthropic.AsyncAnthropic(api_key=self.api_key)

            response = await client.messages.create(
                model=self.llm_model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
            )

            return Ok(response.content[0].text)

        except ImportError:
            return Err("Please install anthropic: pip install anthropic")
        except Exception as e:
            return Err(f"Anthropic LLM Error: {str(e)}")
