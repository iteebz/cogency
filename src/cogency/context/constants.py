"""Context module constants and message structure specification.

Message structure:
- Single system message: instructions + tools + profile + history + task boundary
- Current execution: user query → assistant thinking/calls → system results → assistant response
- History format: past cycles only (N messages before current cycle)
- Off-by-one prevention: exclude current cycle from history to prevent hallucination
"""

# CONVERSATION: Context constants
DEFAULT_CONVERSATION_ID = "ephemeral"  # Fallback for stateless contexts
DEFAULT_USER_ID = "default"  # Fallback user identifier


# CONTEXT: Token limits per model family (leave 20% headroom for generation)
CONTEXT_LIMITS = {
    "gpt-4o": 16000,  # 20k context - 20% headroom
    "gpt-4o-mini": 12800,  # 16k context - 20% headroom
    "gpt-5": 16000,  # 20k context - 20% headroom
    "gpt-5-mini": 12800,  # 16k context - 20% headroom
    "gpt-5-nano": 12800,  # 16k context - 20% headroom
    "o1-mini": 12800,  # 16k context - 20% headroom
    "o3-mini": 12800,  # 16k context - 20% headroom
    "claude-haiku-3.5": 6400,  # 8k context - 20% headroom
    "claude-sonnet-4": 16000,  # 20k context - 20% headroom
    "gemini-2.5-flash": 80000,  # 100k context - 20% headroom
    "gemini-2.5-flash-lite": 80000,
    "models/gemini-2.5-flash-live-preview": 80000,
}
