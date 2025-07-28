"""Deep mode reasoning - structured thinking with reflection, planning, and decision phases."""


def prompt_deep_mode(
    tool_registry: str,
    query: str,
    iteration: int,
    max_iterations: int,
    current_approach: str,
    structured_actions: str,
    latest_results_detail: str,
) -> str:
    """Generate structured prompt for deep mode reasoning."""
    from cogency.constants import MAX_TOOL_CALLS_PER_ITERATION

    return f"""
DEEP: Structured reasoning for query: {query}

CRITICAL: Output ONE JSON object for THIS ITERATION ONLY. Do not anticipate future steps.

JSON Response Format:
{{
  "thinking": "What am I trying to accomplish? What's my approach to this problem?",
  "reflect": "What worked/failed in previous actions? What gaps remain?",
  "plan": "What specific tools to use next and expected outcomes?",
  "tool_calls": [
    {{"name": "tool_a", "args": {{"param": "value"}}}},
    {{"name": "tool_b", "args": {{"param": "value"}}}},
    {{"name": "tool_c", "args": {{"param": "value"}}}}
  ],
  "switch_to": null,
  "switch_why": null
}}

IMPORTANT: All {MAX_TOOL_CALLS_PER_ITERATION} tool calls must be in ONE tool_calls array, not separate JSON objects.

TOOLS:
{tool_registry}

CONTEXT:
Iteration {iteration}/{max_iterations} - Review completed actions to avoid repetition
Current approach: {current_approach}

PREVIOUS ACTIONS:
{structured_actions}

LATEST TOOL RESULTS:
{latest_results_detail}

REASONING PHASES:
🤔 REFLECT: Review completed actions and their DETAILED results - what information do you already have? What gaps remain?
📋 PLAN: Choose NEW tools that address remaining gaps - avoid repeating successful actions
🎯 EXECUTE: Run planned tools sequentially when they address different aspects

RECOVERY ACTIONS:
- Tool parameter errors → Check required vs optional parameters in schema
- No results from tools → Try different parameters or alternative approaches
- Information conflicts → Use additional tools to verify or synthesize  
- Use the DETAILED action history to understand what actually happened, not just success/failure
- Avoid repeating successful tool calls - check action history first
- Empty tool_calls array ([ ]) if query fully answered or no progress possible
- If original query has been fully resolved, say so explicitly and return tool_calls: []
- LIMIT: Maximum {MAX_TOOL_CALLS_PER_ITERATION} tool calls per iteration to avoid JSON parsing issues

DOWNSHIFT to FAST if:
- Simple datetime request using time tool
- Direct search with obvious keywords
- Single-step action with clear tool choice

Examples:
switch_to: "fast", switch_why: "Query simplified to direct search"
switch_to: "fast", switch_why: "Single tool execution sufficient"
"""
