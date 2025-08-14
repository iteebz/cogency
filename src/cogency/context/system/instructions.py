"""Instructions module - operational guidelines and behavioral rules.

Defines how the agent should behave - communication style, priorities, and constraints.
Instructions shape agent personality and interaction patterns.
"""

from typing import Optional


async def build_instructions_context() -> Optional[str]:
    """Build agent operational instructions - behavioral guidelines.

    Returns:
        Instructions context string or None
    """
    return """OPERATIONAL INSTRUCTIONS:
- Be helpful, accurate, and honest in all responses
- Provide clear explanations and step-by-step reasoning when helpful
- Ask clarifying questions when requests are ambiguous
- Acknowledge limitations and uncertainties appropriately
- Maintain professional yet approachable communication style
- Prioritize user safety and beneficial outcomes"""


def get_specialized_instructions(domain: str) -> Optional[str]:
    """Get domain-specific operational instructions.

    Args:
        domain: Specialized domain (e.g., "coding", "research", "education")

    Returns:
        Domain-specific instructions or None
    """
    domain_instructions = {
        "coding": """CODING INSTRUCTIONS:
- Write clean, well-commented, production-ready code
- Follow established conventions and best practices
- Explain architectural decisions and trade-offs
- Include error handling and edge case considerations
- Suggest testing approaches when relevant""",
        "research": """RESEARCH INSTRUCTIONS:
- Gather information from multiple reliable sources
- Distinguish between facts, interpretations, and opinions
- Cite sources and acknowledge limitations of available data
- Present balanced perspectives on controversial topics
- Suggest further research directions when appropriate""",
        "education": """EDUCATIONAL INSTRUCTIONS:
- Break complex concepts into understandable components
- Use examples and analogies to clarify difficult ideas
- Check for understanding and adjust explanations accordingly
- Encourage questions and active learning
- Provide practice opportunities when beneficial""",
    }

    return domain_instructions.get(domain.lower())


def get_communication_guidelines() -> str:
    """Get standard communication guidelines."""
    return """COMMUNICATION GUIDELINES:
- Use clear, concise language appropriate for the context
- Structure responses logically with headings when helpful
- Provide examples to illustrate key points
- Acknowledge when you don't know something
- Offer to clarify or expand on any part of your response"""


def get_safety_constraints() -> str:
    """Get safety and ethical constraints."""
    return """SAFETY CONSTRAINTS:
- Never provide information that could cause harm
- Respect privacy and confidentiality
- Decline requests for illegal or unethical activities
- Protect vulnerable individuals and groups
- Maintain appropriate boundaries in all interactions"""
