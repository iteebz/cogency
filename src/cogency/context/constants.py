"""Context module constants and message structure specification.

Message structure:
- Single system message: instructions + tools + profile + history + task boundary
- Current execution: user query → assistant thinking/calls → system results → assistant response
- History format: past cycles only (N messages before current cycle)
- Off-by-one prevention: exclude current cycle from history to prevent hallucination
"""

# CONVERSATION: History assembly limits
HISTORY_LIMIT = 20  # User/assistant/tools messages to include (excludes 'think' before counting)
DEFAULT_CONVERSATION_ID = "ephemeral"  # Fallback for stateless contexts

# PROFILE: Memory management and learning limits
PROFILE_LIMITS = {
    "compress_threshold": 1000,  # Trigger compression at N chars
    "compress_target": 800,  # Compress down to N chars
    "learning_trigger": 5,  # Check every N new user messages
    "learning_window": 10,  # Learn from last N messages for context
}
