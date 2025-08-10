"""Archive prompts - extraction and merging."""

from cogency.state import State

from ...steps.common import JSON_FORMAT_CORE

EXTRACTION_SYSTEM_PROMPT = f"""Extract valuable technical insights from conversation history.

{JSON_FORMAT_CORE}

Focus on extracting:
- Technical insights, best practices, lessons learned
- Domain knowledge worth preserving long-term
- Problem-solving patterns and solutions
- Implementation details and trade-offs

EXCLUSION CRITERIA:
- Personal information or user-specific preferences
- Temporary context or situational details
- Simple facts available in documentation
- Conversational pleasantries or meta-discussion

QUALITY STANDARDS:
- Minimum insight length: 20 characters
- Confidence threshold: 0.7 or higher
- Clear, transferable knowledge
- Specific and actionable

RESPONSE FORMAT:
{{
  "insights": [
    {{
      "topic": "Python Performance", 
      "insight": "List comprehensions are 2-3x faster than equivalent for loops for simple operations due to reduced function call overhead",
      "confidence": 0.9,
      "context": "performance optimization discussion"
    }}
  ]
}}"""


def build_extraction_prompt(state: State) -> str:
    """Build knowledge extraction prompt from conversation history."""

    # Extract conversation messages - NO ARBITRARY LIMITS
    messages = []
    if state.conversation and state.conversation.messages:
        # Get FULL conversation history per our cleanup goals
        for msg in state.conversation.messages:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            if content and role in ["user", "assistant"]:
                messages.append(f"{role.upper()}: {content}")

    if not messages:
        conversation_text = "No conversation history available."
    else:
        conversation_text = "\n\n".join(messages)

    # Build context
    context = f"""CONVERSATION CONTEXT:
User ID: {state.user_id}
Task: {state.workspace.objective if state.workspace else state.query}
Messages: {len(messages)} exchanges

CONVERSATION HISTORY:
{conversation_text}"""

    return f"""{EXTRACTION_SYSTEM_PROMPT}

{context}

Extract valuable knowledge insights as JSON:"""


MERGE_SYSTEM_PROMPT = """Merge new insights into existing topic documents.

MERGE PRINCIPLES:
- Integrate new insights naturally into existing structure
- Avoid duplication - if insight already exists, don't repeat it
- Organize information logically with clear sections
- Maintain markdown formatting and readability
- Keep tone consistent and concise
- If new insight contradicts existing info, note both perspectives with context
- Update any "Last Updated" timestamps

Return the complete updated document."""


def build_merge_prompt(existing_content: str, new_insight: str) -> str:
    """Build merge prompt for integrating insight with existing document."""

    return f"""{MERGE_SYSTEM_PROMPT}

EXISTING DOCUMENT:
{existing_content}

NEW INSIGHT:
{new_insight}

Updated document:"""
