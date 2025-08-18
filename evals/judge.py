"""Direct LLM judge - zero ceremony evaluation."""

from datetime import datetime
from typing import Dict, Union

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv optional

from cogency.lib.providers import create_llm


def create_judge_llm(provider: Union[str, object] = "openai") -> object:
    """Create judge LLM with provider autodetection."""
    try:
        return create_llm(provider)
    except ValueError:
        # #TODO: Judge provider autodetection not ready - doing manual review
        return None


async def judge(criteria: str, prompt: str, response: str, provider: Union[str, object] = "openai") -> tuple[bool, Dict]:
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
        {"role": "user", "content": evaluation}
    ]
    
    result = await llm.generate(messages)
    
    if result.success:
        judgment = result.unwrap()
        passed = "PASS" in judgment.upper()
        return passed, {"judgment": judgment, "timestamp": datetime.now().isoformat()}
    else:
        return False, {"error": result.error}