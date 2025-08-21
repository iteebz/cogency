"""OpenAI provider - LLM and Embedder protocol implementation."""

from ...core.protocols import LLM, Embedder
from ..result import Err, Ok, Result
from ..rotation import with_rotation


class OpenAI(LLM, Embedder):
    """OpenAI provider implementing LLM and Embedder protocols."""

    def __init__(
        self,
        api_key: str = None,
        llm_model: str = "gpt-4o-mini",
        embed_model: str = "text-embedding-3-small",
        temperature: float = 0.7,
        max_tokens: int = 500,
    ):
        from ..credentials import detect_api_key

        self.api_key = api_key or detect_api_key("openai")
        if not self.api_key:
            raise RuntimeError("No API key found")
        self.llm_model = llm_model
        self.embed_model = embed_model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.client = None  # Set by _get_client() or tests

    def _get_client(self):
        """Get or create OpenAI client."""
        if self.client is None:
            import openai

            self.client = openai.AsyncOpenAI(api_key=self.api_key)
        return self.client

    async def generate(self, messages: list[dict]) -> Result[str, str]:
        """Generate text from conversation messages with key rotation."""
        try:

            async def _generate(api_key: str):
                import openai

                client = openai.AsyncOpenAI(api_key=api_key)
                response = await client.chat.completions.create(
                    model=self.llm_model,
                    messages=messages,
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                )
                return response.choices[0].message.content

            result = await with_rotation("OPENAI", _generate)
            return Ok(result)

        except ImportError:
            return Err("Please install openai: pip install openai")
        except Exception as e:
            return Err(f"OpenAI LLM Error: {str(e)}")

    async def embed(self, texts: list[str]) -> Result[list[list[float]], str]:
        """Generate embeddings for input texts with key rotation."""
        try:

            async def _embed(api_key: str):
                import openai

                client = openai.AsyncOpenAI(api_key=api_key)
                response = await client.embeddings.create(model=self.embed_model, input=texts)
                return [item.embedding for item in response.data]

            result = await with_rotation("OPENAI", _embed)
            return Ok(result)

        except ImportError:
            return Err("Please install openai: pip install openai")
        except Exception as e:
            return Err(f"OpenAI Embedder Error: {str(e)}")
