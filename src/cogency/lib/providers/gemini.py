"""Gemini provider - LLM and Embedder protocol implementation."""

from ...core.protocols import LLM, Embedder
from ..result import Err, Ok, Result


class Gemini(LLM, Embedder):
    """Gemini provider implementing LLM and Embedder protocols."""

    def __init__(
        self,
        api_key: str,
        llm_model: str = "gemini-2.5-flash-lite",
        embed_model: str = "gemini-embedding-001",
        temperature: float = 0.7,
    ):
        self.api_key = api_key
        self.llm_model = llm_model
        self.embed_model = embed_model
        self.temperature = temperature

    async def generate(self, messages: list[dict]) -> Result[str, str]:
        """Generate text from conversation messages."""
        try:
            import google.generativeai as genai

            genai.configure(api_key=self.api_key)
            model = genai.GenerativeModel(self.llm_model)

            # Convert messages to Gemini format
            prompt = "\n".join([f"{msg['role']}: {msg['content']}" for msg in messages])

            response = await model.generate_content_async(
                prompt, generation_config=genai.types.GenerationConfig(temperature=self.temperature)
            )

            return Ok(response.text)

        except ImportError:
            return Err("Please install google-generativeai: pip install google-generativeai")
        except Exception as e:
            return Err(f"Gemini LLM Error: {str(e)}")

    async def embed(self, texts: list[str]) -> Result[list[list[float]], str]:
        """Generate embeddings for input texts."""
        try:
            import google.generativeai as genai

            genai.configure(api_key=self.api_key)

            embeddings = []
            for text in texts:
                result = genai.embed_content(model=self.embed_model, content=text)
                embeddings.append(result["embedding"])

            return Ok(embeddings)

        except ImportError:
            return Err("Please install google-generativeai: pip install google-generativeai")
        except Exception as e:
            return Err(f"Gemini Embedder Error: {str(e)}")
