"""System subdomain - agent identity, boundaries, and operational constraints.

The system domain defines who the agent is and what it can do:
- Identity: Agent persona and role
- Security: Safety boundaries and threat protection
- Capabilities: Available tools and functions
- Instructions: Operational guidelines and behavior

Constitutional principle: Agent knows itself - identity, limits, and purpose.
"""

from .identity import build_identity_context
from .instructions import build_instructions_context
from .security import (
    SecurityBoundary,
    SecurityResult,
    build_security_context,
    validate_query_semantic,
)


async def build_system_context(
    identity: str = "AI Assistant",
    iteration: int = 1,
    tools: list = None,
    security_level: str = "standard",
) -> str | None:
    """Build complete system context - canonical agent self-definition.

    Assembles agent identity, security boundaries, capabilities, and instructions
    into unified system context. Only includes security assessment on first iteration.

    Args:
        identity: Agent role and persona
        iteration: Current reasoning iteration
        tools: Available tool instances
        security_level: Security boundary enforcement level

    Returns:
        System context string or None
    """
    parts = []

    # Identity - who we are
    identity_context = await build_identity_context(identity)
    if identity_context:
        parts.append(identity_context)

    # Security - what we protect against (iteration 1 only)
    if iteration == 1:
        security_context = await build_security_context(security_level)
        if security_context:
            parts.append(security_context)

    # Capabilities - use tool registry directly
    if tools:
        tool_descriptions = [
            f"- {tool.name}: {tool.description}"
            for tool in tools
            if hasattr(tool, "name") and hasattr(tool, "description")
        ]
        if tool_descriptions:
            parts.append("CAPABILITIES:\n" + "\n".join(tool_descriptions))

    # Instructions - how we behave
    instructions_context = await build_instructions_context()
    if instructions_context:
        parts.append(instructions_context)

    return "\n\n".join(parts) if parts else None


__all__ = [
    "build_system_context",
    "build_identity_context",
    "build_security_context",
    "build_instructions_context",
    "SecurityBoundary",
    "SecurityResult",
    "validate_query_semantic",
]
