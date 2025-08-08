"""Synthesis prompts - user understanding consolidation."""

from typing import Any, Dict

from cogency.state import State

from ..common import JSON_FORMAT_CORE

SYNTHESIS_SYSTEM_PROMPT = f"""You are a user understanding synthesizer. Build comprehensive psychological profiles from interactions.

{JSON_FORMAT_CORE}

Your synthesis should capture:
- **Preferences**: Technical choices, work styles, communication preferences
- **Goals**: What the user is trying to achieve (short-term and long-term)
- **Expertise**: Technical skills, domain knowledge, experience level
- **Context**: Current projects, constraints, environment
- **Communication Style**: How they prefer to receive information
- **Learning Patterns**: How they approach new problems

SYNTHESIS PRINCIPLES:
1. **Evidence-based**: Only include insights supported by interaction data
2. **Evolving**: Update existing understanding, don't replace wholesale
3. **Actionable**: Focus on insights that improve future interactions
4. **Respectful**: Maintain user privacy and dignity
5. **Contextual**: Consider the user's current situation and goals

RESPONSE FORMAT:
{{
  "preferences": {{"language": "", "framework": "", "approach": "", "communication": ""}},
  "goals": ["objectives"],
  "expertise": ["knowledge areas"], 
  "context": {{"project": "", "constraints": "", "environment": ""}},
  "communication_style": "interaction approach",
  "learning_patterns": "problem-solving style",
  "synthesis_notes": "key insights"
}}"""


def build_synthesis_prompt(interaction_data: Dict[str, Any], state: State) -> str:
    """Build synthesis prompt with flat state context."""

    # Extract interaction details
    current_query = interaction_data.get("query", state.query)
    current_response = interaction_data.get("response", state.execution.response or "")
    success = interaction_data.get("success", True)

    # Build existing understanding from flat state
    existing_understanding = ""
    if hasattr(state, "preferences") and state.preferences:
        existing_understanding += f"CURRENT PREFERENCES: {state.preferences}\n"
    if hasattr(state, "goals") and state.goals:
        existing_understanding += f"CURRENT GOALS: {state.goals}\n"
    if hasattr(state, "expertise") and state.expertise:
        existing_understanding += f"CURRENT EXPERTISE: {state.expertise}\n"
    if hasattr(state, "communication_style") and state.communication_style:
        existing_understanding += f"COMMUNICATION STYLE: {state.communication_style}\n"

    if not existing_understanding:
        existing_understanding = "EXISTING UNDERSTANDING: None - first synthesis"

    # Build interaction context
    interaction_context = f"""CURRENT INTERACTION:
Query: {current_query}
Response: {current_response}
Success: {success}
Complexity: {state.iteration} iterations
Tools Used: {len(state.tool_calls)} tools"""

    # Build session context
    session_context = f"""SESSION CONTEXT:
Total Messages: {len(state.messages)}
User ID: {state.user_id}"""

    return f"""{SYNTHESIS_SYSTEM_PROMPT}

{existing_understanding}

{interaction_context}

{session_context}

Based on this interaction and existing understanding, synthesize an updated user profile. Focus on what this interaction reveals about the user's preferences, goals, expertise, and communication style.

Provide synthesis as JSON:"""
