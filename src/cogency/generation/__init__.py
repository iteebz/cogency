"""Response generation and formatting utilities."""
from .shaper import ResponseShaper, SHAPING_PROFILES, shape_response
from .prompt_composer import compose_system_prompt

__all__ = [
    "ResponseShaper",
    "SHAPING_PROFILES", 
    "shape_response",
    "compose_system_prompt",
]