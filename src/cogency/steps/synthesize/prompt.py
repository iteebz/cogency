"""Synthesis prompts - user understanding consolidation."""

from typing import Any, Dict

from cogency.state import AgentState, UserProfile

SYNTHESIS_SYSTEM_PROMPT = """You are a user understanding synthesizer. Your role is to build a comprehensive psychological profile of the user based on their interactions.

CRITICAL: Output valid JSON only - no markdown, no explanations, just the JSON object.

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
{
  "preferences": {
    "language": "primary programming language",
    "framework": "preferred frameworks/tools",
    "approach": "problem-solving style",
    "communication": "preferred communication style"
  },
  "goals": [
    "specific objectives the user is working toward"
  ],
  "expertise": [
    "areas of demonstrated knowledge and skill"
  ],
  "context": {
    "current_project": "what they're working on now",
    "constraints": "limitations or challenges they face",
    "environment": "work/development environment"
  },
  "communication_style": "how to best communicate with this user",
  "learning_patterns": "how they approach learning and problem-solving",
  "synthesis_notes": "key insights about this user's needs and preferences"
}"""


def build_synthesis_prompt(
    user_profile: UserProfile, interaction_data: Dict[str, Any], state: AgentState
) -> str:
    """Build synthesis prompt with user context."""

    # Extract current interaction details
    current_query = interaction_data.get("query", "")
    current_response = interaction_data.get("response", "")
    success = interaction_data.get("success", True)

    # Build existing understanding context
    existing_understanding = ""
    if user_profile:
        if hasattr(user_profile, "preferences") and user_profile.preferences:
            existing_understanding += f"CURRENT PREFERENCES: {user_profile.preferences}\n"
        if hasattr(user_profile, "goals") and user_profile.goals:
            existing_understanding += f"CURRENT GOALS: {user_profile.goals}\n"
        if hasattr(user_profile, "expertise") and user_profile.expertise:
            existing_understanding += f"CURRENT EXPERTISE: {user_profile.expertise}\n"
        if hasattr(user_profile, "communication_style") and user_profile.communication_style:
            existing_understanding += f"COMMUNICATION STYLE: {user_profile.communication_style}\n"

    if not existing_understanding:
        existing_understanding = "EXISTING UNDERSTANDING: None - this is the first synthesis"

    # Build interaction context
    interaction_context = f"""CURRENT INTERACTION:
Query: {current_query}
Response: {current_response}
Success: {success}
Complexity: {state.execution.iteration} iterations
Tools Used: {len(getattr(state.execution, 'completed_calls', []))} tools"""

    # Build session context
    session_context = f"""SESSION CONTEXT:
Total Interactions: {user_profile.interaction_count if user_profile else 1}
User ID: {state.execution.user_id}"""

    return f"""{SYNTHESIS_SYSTEM_PROMPT}

{existing_understanding}

{interaction_context}

{session_context}

Based on this interaction and existing understanding, synthesize an updated user profile. Focus on what this interaction reveals about the user's preferences, goals, expertise, and communication style.

Provide your synthesis as a JSON object:"""
