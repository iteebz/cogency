"""Fast mode reasoning - streamlined ReAct for direct execution."""


def prompt_fast_mode(tool_registry: str, query: str, attempts_summary: str = "") -> str:
    """Streamlined ReAct prompt for fast mode execution."""
    from cogency.constants import MAX_TOOL_CALLS_PER_ITERATION

    return f"""
FAST: Direct execution for query: {query}

CRITICAL: Output ONE JSON object for THIS ITERATION ONLY. Do not anticipate future steps.

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


CRITICAL STOP CONDITIONS:
- If you see previous attempts that ALREADY answered the query → tool_calls: []
- If query is fully satisfied by previous results → tool_calls: []  
- If no tool can help with this query → tool_calls: []
- If repeating same failed action → tool_calls: []

GUIDANCE:
- FIRST: Review previous attempts to avoid repeating actions
- Use tools only if query needs MORE information
- LIMIT: Maximum {MAX_TOOL_CALLS_PER_ITERATION} tool calls per iteration

ESCALATE to DEEP if encountering:
- Tool results conflict and need synthesis
- Multi-step reasoning chains required  
- Ambiguous requirements need breakdown
- Complex analysis beyond direct execution

Examples:
switch_to: "deep", switch_why: "Search results contradict, need analysis"
switch_to: "deep", switch_why: "Multi-step calculation required"
"""
