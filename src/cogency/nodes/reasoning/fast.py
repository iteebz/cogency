"""Fast mode reasoning - streamlined ReAct for direct execution."""


def prompt_fast_mode(tool_registry: str, query: str, attempts_summary: str = "") -> str:
    """Streamlined ReAct prompt for fast mode execution."""
    from cogency.constants import MAX_TOOL_CALLS_PER_ITERATION

    return f"""
FAST: Direct execution for query: {query}

CRITICAL: Output EXACTLY ONE JSON object. Do NOT generate multiple JSON objects or responses.

REQUIRED JSON Response Format (ALWAYS return valid JSON):
{{
  "thinking": "quick reasoning about next action",
  "tool_calls": [
    {{"name": "tool1", "args": {{"param": "value"}}}},
    {{"name": "tool2", "args": {{"param": "value"}}}},
    {{"name": "tool3", "args": {{"param": "value"}}}}
  ],
  "switch_to": null,
  "switch_why": null
}}

IMPORTANT: All {MAX_TOOL_CALLS_PER_ITERATION} tool calls must be in ONE tool_calls array, not separate JSON objects.

When done: {{"thinking": "explanation", "tool_calls": [], "switch_to": null, "switch_why": null}}

TOOLS:
{tool_registry}

PREVIOUS CONTEXT:
{attempts_summary if attempts_summary else "Initial execution - no prior actions"}

GUIDANCE:
- Review previous iterations (if any) before deciding next actions
- Use multiple sequential tools when they address different aspects
- Empty tool_calls array ([ ]) if query fully answered or no suitable tools
- If original query has been fully resolved, return tool_calls: []
- LIMIT: Maximum {MAX_TOOL_CALLS_PER_ITERATION} tool calls per iteration to avoid JSON parsing issues

ESCALATE to DEEP if encountering:
- Tool results conflict and need synthesis
- Multi-step reasoning chains required  
- Ambiguous requirements need breakdown
- Complex analysis beyond direct execution

Examples:
switch_to: "deep", switch_why: "Search results contradict, need analysis"
switch_to: "deep", switch_why: "Multi-step calculation required"
"""
