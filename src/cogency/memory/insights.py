"""Interaction insight extraction utilities."""

from typing import Any, Dict

from cogency.utils.parsing import _parse_json


async def extract_insights(llm, interaction_data: Dict[str, Any]) -> Dict[str, Any]:
    """Extract insights from single interaction."""

    query = interaction_data.get("query", "")
    response = interaction_data.get("response", "")
    success = interaction_data.get("success", True)

    prompt = f"""Extract user insights from this interaction:

User Query: {query}
Agent Response: {response}
Success: {success}

Extract specific insights:
- Preferences: Key-value pairs of user preferences
- Goals: What is the user trying to build/achieve?
- Expertise: Areas of knowledge and skill
- Communication: Prefers concise vs detailed explanations
- Project: Name, domain, current focus area
- Patterns: What types of requests succeed/fail?

Return JSON:
{{
    "preferences": {{"key": "value"}},
    "goals": ["goal1", "goal2"],
    "expertise": ["area1", "area2"],
    "communication_style": "concise|detailed|technical",
    "project_context": {{"project_name": "description"}},
    "success_pattern": "what worked",
    "failure_pattern": "what didn't work"
}}"""

    result = await llm.run([{"role": "user", "content": prompt}])
    if result.success:
        parsed = _parse_json(result.data)
        return parsed.data if parsed.success else {}
    return {}
