"""Response shaping helper for ReAct loop."""
from typing import Dict, Any, Optional
from cogency.llm import BaseLLM


async def apply_response_shaping(text: str, llm: BaseLLM, shaper_config: Optional[Dict[str, Any]]) -> str:
    """Apply response shaping if configured, otherwise return text unchanged."""
    if not shaper_config:
        return text
    
    from cogency.response_shaper import ResponseShaper
    shaper = ResponseShaper(llm)
    return await shaper.shape(text, shaper_config)