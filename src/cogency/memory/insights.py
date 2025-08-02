"""Interaction insight extraction utilities."""

from typing import Any, Dict

from cogency.utils import parse_json


async def extract_insights(llm, interaction_data: Dict[str, Any]) -> Dict[str, Any]:
    """Extract insights from single interaction."""

    query = interaction_data.get("query", "")
    response = interaction_data.get("response", "")
    success = interaction_data.get("success", True)

    prompt = f"""Extract user insights from this interaction:

User Query: {query}
Agent Response: {response}
Success: {success}

Extract insights about:
- User goals and preferences
- Technical expertise level  
- Communication preferences
- Project context
- Success/failure patterns

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
        parsed = parse_json(result.data)
        return parsed.data if parsed.success else {}
    return {}
