"""Profile synthesis - user understanding parsing and updates."""

import json
from datetime import datetime
from typing import Any, Dict, Optional

from cogency.events import emit


def parse_synthesis_response(response: str) -> Optional[Dict[str, Any]]:
    """Parse LLM synthesis response into structured data."""
    try:
        # Clean the response - remove any markdown formatting
        clean_response = response.strip()
        if clean_response.startswith("```json"):
            clean_response = clean_response[7:]
        if clean_response.endswith("```"):
            clean_response = clean_response[:-3]

        # Parse JSON
        synthesis_data = json.loads(clean_response.strip())
        return synthesis_data

    except (json.JSONDecodeError, ValueError) as e:
        emit("synthesis_parse_error", error=str(e), response_preview=response[:200])
        return None


def apply_synthesis_to_profile(user_profile, synthesis_data: Dict[str, Any]):
    """Apply synthesis impressions to user profile."""
    # Update preferences
    if "preferences" in synthesis_data:
        user_profile.preferences = {
            **(user_profile.preferences or {}),
            **synthesis_data["preferences"],
        }

    # Update goals (merge with existing)
    if "goals" in synthesis_data:
        existing_goals = set(user_profile.goals or [])
        new_goals = set(synthesis_data["goals"])
        user_profile.goals = list(existing_goals | new_goals)

    # Update expertise (merge with existing)
    if "expertise" in synthesis_data:
        existing_expertise = set(user_profile.expertise or [])
        new_expertise = set(synthesis_data["expertise"])
        user_profile.expertise = list(existing_expertise | new_expertise)

    # Update communication style
    if "communication_style" in synthesis_data:
        user_profile.communication_style = synthesis_data["communication_style"]

    # Store synthesis metadata
    user_profile.last_synthesis_time = datetime.now().isoformat()
    user_profile.synthesis_version = getattr(user_profile, "synthesis_version", 0) + 1
