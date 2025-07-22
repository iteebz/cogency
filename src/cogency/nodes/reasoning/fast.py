"""Fast mode reasoning - streamlined ReAct for direct execution."""

from typing import Dict, Optional

from cogency.utils import parse_json


def prompt_fast_mode(tool_info: str, query: str) -> str:
    """Streamlined ReAct prompt for fast mode execution."""
    from cogency.nodes.reasoning.adaptive import get_switching_criteria

    return f"""FAST MODE: Direct ReAct execution for simple tasks.

QUERY: {query}
TOOLS: {tool_info}

Think → Act → Observe. Use tools if needed.

{get_switching_criteria("fast")}
"""


def parse_fast_mode(response: str) -> Dict[str, Optional[str]]:
    """Extract structured data from fast mode LLM response."""
    try:
        json_data = parse_json(response)
        if json_data:
            return {
                "thinking": json_data.get("thinking"),
                "decision": json_data.get("decision"),
                "switch_to": json_data.get("switch_to"),
                "switch_why": json_data.get("switch_why"),
            }
    except Exception:
        pass

    return {
        "thinking": "Analyzing the request and determining approach",
        "decision": "Proceeding with direct execution",
        "switch_to": None,
        "switch_why": None,
    }


def format_fast_mode(data: Dict[str, Optional[str]]) -> str:
    """Format fast mode thinking for display."""
    parts = []

    if data.get("thinking"):
        parts.append(f"💭 {data['thinking']}")

    if data.get("decision"):
        parts.append(f"⚡ {data['decision']}")

    return " | ".join(parts) if parts else "Processing request..."
