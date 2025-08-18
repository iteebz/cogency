"""OpenAI provider - isolated LLM integration."""

import os
from typing import Optional

# Load environment variables
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass


async def generate(prompt: str, model: str = "gpt-4o-mini") -> str:
    """Generate LLM response - pure function."""
    try:
        import openai

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return "Please set OPENAI_API_KEY environment variable."

        client = openai.AsyncOpenAI(api_key=api_key)

        response = await client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,
            temperature=0.7,
        )

        return response.choices[0].message.content

    except ImportError:
        return "Please install openai: pip install openai"
    except Exception as e:
        return f"LLM Error: {str(e)}"


async def embed(text: str) -> Optional[list]:
    """Generate embedding - pure function."""
    try:
        import openai

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return None

        client = openai.OpenAI(api_key=api_key)
        response = client.embeddings.create(model="text-embedding-3-small", input=text)

        return response.data[0].embedding

    except Exception:
        return None
