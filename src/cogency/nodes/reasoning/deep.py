"""Deep mode reasoning - structured thinking with reflection, planning, and decision phases."""

from typing import Dict, Optional


def prompt_deep_mode(
    tool_info: str,
    query: str,
    current_iteration: int,
    max_iterations: int,
    current_approach: str,
    previous_attempts: str,
    last_tool_quality: str,
) -> str:
    """Generate structured prompt for deep mode reasoning.

    Uses REFLECTION → PLANNING → DECISION structure for complex analysis.
    """
    from cogency.nodes.reasoning.adaptive import get_switching_criteria

    return f"""DEEP MODE: Structured reasoning for complex analysis and multi-step tasks.

ORIGINAL QUERY: {query}
AVAILABLE TOOLS: {tool_info}

ITERATION: {current_iteration}/{max_iterations}
CURRENT APPROACH: {current_approach}
PREVIOUS ATTEMPTS: {previous_attempts}
LAST TOOL QUALITY: {last_tool_quality}

Use structured reasoning phases:

[REFLECTION]
What have I learned so far? What patterns do I see? What's working/not working?

[PLANNING]
Based on my reflection, what's my multi-step approach?
- Break down the problem if complex
- Identify key information needed
- Plan tool usage sequence
- Consider potential obstacles

[DECISION]
This is what I've decided to do and why.

Downshift to FAST MODE if this task is simpler than expected.

{get_switching_criteria("deep")}

Use tools if needed or provide direct response if you can answer completely."""


def parse_deep_mode(llm_response: str) -> Dict[str, Optional[str]]:
    """Extract structured thinking phases from LLM response (reflection, planning, decision)."""
    try:
        import re

        from cogency.utils import parse_json

        data = parse_json(llm_response)
        if data:
            thinking = data.get("thinking")
            if isinstance(thinking, dict):
                return {
                    "reflection": thinking.get("reflection"),
                    "planning": thinking.get("planning"),
                    "decision": thinking.get("decision"),
                    "switch_to": data.get("switch_to"),
                    "switch_why": data.get("switch_why"),
                }
            # Fallback for old flat format
            elif "reflection" in data or "planning" in data or "decision" in data:
                return {
                    "reflection": data.get("reflection"),
                    "planning": data.get("planning"),
                    "decision": data.get("decision"),
                    "switch_to": data.get("switch_to"),
                    "switch_why": data.get("switch_why"),
                }

        # Try text-based patterns for reflection, planning, decision
        reflection_match = re.search(
            r"^\s*\[REFLECTION\]\s*(.*?)(?=\n\s*\[PLANNING\]|\n\s*\[DECISION\]|$)",
            llm_response,
            re.DOTALL | re.MULTILINE,
        )
        planning_match = re.search(
            r"^\s*\[PLANNING\]\s*(.*?)(?=\n\s*\[DECISION\]|$)",
            llm_response,
            re.DOTALL | re.MULTILINE,
        )
        decision_match = re.search(
            r"^\s*\[DECISION\]\s*(.*)", llm_response, re.DOTALL | re.MULTILINE
        )

        if reflection_match or planning_match or decision_match:
            return {
                "reflection": reflection_match.group(1).strip() if reflection_match else None,
                "planning": planning_match.group(1).strip() if planning_match else None,
                "decision": decision_match.group(1).strip() if decision_match else None,
                "switch_to": None,
                "switch_why": None,
            }

    except Exception:
        pass
    return {
        "reflection": None,
        "planning": None,
        "decision": None,
        "switch_to": None,
        "switch_why": None,
    }


def format_deep_mode(phases: Dict[str, Optional[str]]) -> str:
    """Format deep mode phases for human-readable display.

    Args:
        phases: Dict with deep mode phases (reflection, planning, decision)

    Returns:
        Formatted string for streaming/display
    """
    parts = []

    if phases.get("reflection"):
        parts.append(f"🤔 REFLECTION: {phases['reflection']}")

    if phases.get("planning"):
        parts.append(f"📋 PLANNING: {phases['planning']}")

    if phases.get("decision"):
        parts.append(f"🎯 DECISION: {phases['decision']}")

    return "\n\n".join(parts) if parts else "Thinking through the problem..."
