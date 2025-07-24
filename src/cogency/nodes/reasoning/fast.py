"""Fast mode reasoning - streamlined ReAct for direct execution."""


def prompt_fast_mode(tool_registry: str, query: str, attempts_summary: str = "") -> str:
    """Streamlined ReAct prompt for fast mode execution."""

    return f"""
FAST: Direct execution for query: {query}

JSON Response Format:
{{
  "thinking": "quick reasoning about next action",
  "tool_calls": [
    {{"name": "tool1", "args": {{"param": "value"}}}}
  ],
  "switch_to": null,
  "switch_why": null
}}

TOOLS:
{tool_registry}

PREVIOUS CONTEXT:
{attempts_summary if attempts_summary else "Initial execution - no prior actions"}

GUIDANCE:
- Review previous iterations (if any) before deciding next actions
- Use parallel tools when they address independent aspects
- Empty tool_calls array ([ ]) if query fully answered or no suitable tools
- If original query has been fully resolved, say so explicitly and return tool_calls: []

ESCALATE to DEEP if encountering:
- Tool results conflict and need synthesis
- Multi-step reasoning chains required  
- Ambiguous requirements need breakdown
- Complex analysis beyond direct execution

Examples:
switch_to: "deep", switch_why: "Search results contradict, need analysis"
switch_to: "deep", switch_why: "Multi-step calculation required"
"""
