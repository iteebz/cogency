"""Direct LLM judge - zero ceremony evaluation."""

from datetime import datetime
from typing import Union

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass  # dotenv optional

from cogency.lib.credentials import detect_api_key
from cogency.lib.providers import Anthropic, Gemini, OpenAI


def create_judge_llm(provider: Union[str, object] = "openai") -> object:
    """Create judge LLM with provider autodetection."""
    try:
        if isinstance(provider, str):
            if provider.lower() in ["openai", "gpt"]:
                api_key = detect_api_key("openai")
                if not api_key:
                    raise ValueError("OpenAI API key not found. Set OPENAI_API_KEY.")
                return OpenAI(api_key=api_key)
            if provider.lower() in ["anthropic", "claude"]:
                api_key = detect_api_key("anthropic")
                if not api_key:
                    raise ValueError("Anthropic API key not found. Set ANTHROPIC_API_KEY.")
                return Anthropic(api_key=api_key)
            if provider.lower() in ["gemini", "google"]:
                api_key = detect_api_key("gemini")
                if not api_key:
                    raise ValueError(
                        "Gemini API key not found. Set GEMINI_API_KEY or GOOGLE_API_KEY."
                    )
                return Gemini(api_key=api_key)
            raise ValueError(f"Unknown provider: {provider}")
        return provider
    except ValueError:
        # #TODO: Judge provider autodetection not ready - doing manual review
        return None


async def judge(
    criteria: str, prompt: str, response: str, provider: Union[str, object] = "openai"
) -> tuple[bool, dict]:
    """Direct LLM judge - configurable provider with autodetection."""
    llm = create_judge_llm(provider)

    if llm is None:
        return False, {"error": "LLM judge not configured - using manual review"}

    evaluation = f"""CRITERIA: {criteria}
PROMPT: {prompt}
RESPONSE: {response}

Did the agent meet the criteria? Answer PASS or FAIL with reasoning."""

    messages = [
        {"role": "system", "content": "You are an evaluation judge."},
        {"role": "user", "content": evaluation},
    ]

    result = await llm.generate(messages)

    if result.success:
        judgment = result.unwrap()
        passed = "PASS" in judgment.upper()
        return passed, {"judgment": judgment, "timestamp": datetime.now().isoformat()}
    return False, {"error": result.error}
