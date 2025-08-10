"""Situate memory - user profile context injection.

Handles user profile updates and context injection:
- Process user interactions into profile impressions
- Update user preferences and behavioral patterns
- Provide situated context for LLM prompts
"""

from .core import situate

__all__ = ["situate"]
