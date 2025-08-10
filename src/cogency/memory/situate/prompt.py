"""Profile synthesis prompts."""

from cogency.state import State

from ...steps.common import JSON_FORMAT_CORE


def build_synthesis_prompt(interaction_data, state: State) -> str:
    """Build profile update prompt from interaction data."""

    # Extract conversation context
    query = interaction_data.get("query", "")
    response = interaction_data.get("response", "")

    # Build user context from state
    user_profile = state.profile
    current_preferences = user_profile.preferences if user_profile else {}
    current_goals = user_profile.goals if user_profile else []
    current_expertise = user_profile.expertise if user_profile else []
    current_style = user_profile.communication_style if user_profile else ""

    context = f"""INTERACTION DATA:
Query: {query}
Response: {response}

CURRENT PROFILE:
Preferences: {current_preferences}
Goals: {current_goals}
Expertise: {current_expertise}
Communication Style: {current_style}"""

    system_prompt = f"""Analyze interactions to update user profile insights.

{JSON_FORMAT_CORE}

Focus on extracting:
- User preferences and working styles
- Professional goals and interests  
- Technical expertise and knowledge areas
- Communication preferences

RESPONSE FORMAT:
{{
  "preferences": {{"key": "value"}},
  "goals": ["goal1", "goal2"],
  "expertise": ["skill1", "skill2"], 
  "communication_style": "description"
}}

Only include fields where you have clear evidence from the interaction. Empty fields should be omitted."""

    return f"""{system_prompt}

{context}

Extract profile updates as JSON:"""
