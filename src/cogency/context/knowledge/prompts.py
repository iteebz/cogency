"""Knowledge extraction prompts - sophisticated LLM synthesis."""

EXTRACTION_SYSTEM_PROMPT = """Extract valuable technical knowledge from conversation history.

Focus on extracting:
- Technical knowledge, best practices, lessons learned
- Domain knowledge worth preserving long-term
- Problem-solving patterns and solutions
- Implementation details and trade-offs

EXCLUSION CRITERIA:
- Personal information or user-specific preferences
- Temporary context or situational details
- Simple facts available in documentation
- Conversational pleasantries or meta-discussion

QUALITY STANDARDS:
- Minimum knowledge length: 20 characters
- Clear, transferable knowledge
- Specific and actionable
- High confidence (0.7+)

RESPONSE FORMAT:
{
  "knowledge": [
    {
      "topic": "Python Performance",
      "knowledge": "List comprehensions are 2-3x faster than equivalent for loops for simple operations due to reduced function call overhead",
      "confidence": 0.9,
      "context": "performance optimization discussion"
    }
  ]
}"""


def build_extraction_prompt(query: str, response: str, user_id: str) -> str:
    """Build knowledge extraction prompt from conversation."""

    conversation_text = f"""USER: {query}

ASSISTANT: {response}"""

    return f"""{EXTRACTION_SYSTEM_PROMPT}

CONVERSATION CONTEXT:
User ID: {user_id}
Conversation: Single query-response exchange

CONVERSATION HISTORY:
{conversation_text}

Extract valuable knowledge as JSON:"""


MERGE_SYSTEM_PROMPT = """Merge new knowledge into existing topic documents.

MERGE PRINCIPLES:
- Integrate new knowledge naturally into existing structure
- Avoid duplication - if knowledge already exists, don't repeat it
- Organize information logically with clear sections
- Keep tone consistent and concise
- If new knowledge contradicts existing info, note both perspectives with context
- Update timestamps

Return the complete updated document."""


def build_merge_prompt(existing_content: str, new_knowledge: str) -> str:
    """Build merge prompt for integrating knowledge with existing artifact."""

    return f"""{MERGE_SYSTEM_PROMPT}

EXISTING KNOWLEDGE:
{existing_content}

NEW KNOWLEDGE TO INTEGRATE:
{new_knowledge}

Updated knowledge content:"""
