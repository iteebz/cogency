"""Identity module - agent persona and role definition.

Defines who the agent is - role, capabilities, and behavioral characteristics.
Identity shapes all agent interactions and responses.
"""

from typing import Optional


async def build_identity_context(identity: str = "AI Assistant") -> Optional[str]:
    """Build agent identity context - canonical self-definition.

    Args:
        identity: Agent role and persona description

    Returns:
        Identity context string or None
    """
    if not identity or identity.strip() == "":
        return None

    return f"IDENTITY: {identity.strip()}"


def get_default_identity() -> str:
    """Get default agent identity."""
    return "AI Assistant - helpful, harmless, and honest"


def get_specialized_identity(role: str) -> str:
    """Get specialized identity for specific roles.

    Args:
        role: Specialized role (e.g., "coder", "analyst", "researcher")

    Returns:
        Role-specific identity string
    """
    role_identities = {
        "coder": "Software Engineer - expert in code, architecture, and development best practices",
        "analyst": "Data Analyst - skilled in analysis, interpretation, and insight extraction",
        "researcher": "Research Assistant - thorough investigation and evidence-based conclusions",
        "writer": "Writing Assistant - clear communication and compelling content creation",
        "tutor": "Educational Tutor - patient teaching and concept explanation",
    }

    return role_identities.get(role.lower(), get_default_identity())
