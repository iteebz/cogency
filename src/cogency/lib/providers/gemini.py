"""Gemini provider - LLM and Embedder protocol implementation."""

from ...core.protocols import LLM, Embedder
from ..result import Err, Ok, Result
from ..rotation import with_rotation


class Gemini(LLM, Embedder):
    """Gemini provider implementing LLM and Embedder protocols."""

    def __init__(
        self,
        api_key: str = None,
        llm_model: str = "gemini-2.5-flash",
        embed_model: str = "gemini-embedding-001",
        temperature: float = 0.7,
    ):
        from ..credentials import detect_api_key

        self.api_key = api_key or detect_api_key("gemini")
        self.llm_model = llm_model
        self.embed_model = embed_model
        self.temperature = temperature

    async def generate(self, messages: list[dict]) -> Result[str, str]:
        """Generate text from conversation messages with automatic key rotation."""
        try:

            async def _generate(api_key: str):
                import google.genai as genai

                client = genai.Client(api_key=api_key)

                prompt = "\n".join([f"{msg['role']}: {msg['content']}" for msg in messages])

                response = client.models.generate_content(model=self.llm_model, contents=prompt)

                return response.text

            result = await with_rotation("GEMINI", _generate)
            return Ok(result)

        except ImportError:
            return Err("Please install google-genai: pip install google-genai")
        except Exception as e:
            return Err(f"Gemini LLM Error: {str(e)}")

    async def embed(self, texts: list[str]) -> Result[list[list[float]], str]:
        """Generate embeddings for input texts."""
        try:

            async def _embed(api_key: str):
                import google.genai as genai

                client = genai.Client(api_key=api_key)

                embeddings = []
                for text in texts:
                    result = client.models.embed_content(model=self.embed_model, content=text)
                    embeddings.append(result.embedding)

                return embeddings

            result = await with_rotation("GEMINI", _embed)
            return Ok(result)

        except ImportError:
            return Err("Please install google-genai: pip install google-genai")
        except Exception as e:
            return Err(f"Gemini Embedder Error: {str(e)}")
