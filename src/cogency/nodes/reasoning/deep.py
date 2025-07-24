"""Deep mode reasoning - structured thinking with reflection, planning, and decision phases."""


def prompt_deep_mode(
    tool_registry: str,
    query: str,
    current_iteration: int,
    max_iterations: int,
    current_approach: str,
    previous_attempts: str,
    last_tool_quality: str,
) -> str:
    """Generate structured prompt for deep mode reasoning."""

    return f"""
DEEP: Structured reasoning for query: {query}

JSON Response Format:
{{
  "reflect": "What worked/failed in previous actions? What gaps remain?",
  "plan": "What specific tools to use next and expected outcomes?",
  "tool_calls": [
    {{"name": "tool_a", "args": {{"param": "value"}}}}
  ],
  "switch_to": null,
  "switch_why": null
}}

TOOLS:
{tool_registry}

CONTEXT:
Iteration {current_iteration}/{max_iterations} - Review completed actions to avoid repetition
Current approach: {current_approach}
Action history: {previous_attempts}
Last quality: {last_tool_quality}

REASONING PHASES:
🤔 REFLECT: Review completed actions and their results - what information do you already have? What gaps remain?
📋 PLAN: Choose NEW tools that address remaining gaps - avoid repeating successful actions
🎯 EXECUTE: Run planned tools in parallel when they address independent aspects

RECOVERY ACTIONS:
- Tool parameter errors → Check required vs optional parameters in schema
- No results from tools → Try different parameters or alternative approaches
- Information conflicts → Use additional tools to verify or synthesize  
- Avoid repeating successful tool calls - check action history first
- Empty tool_calls array ([ ]) if query fully answered or no progress possible
- If original query has been fully resolved, say so explicitly and return tool_calls: []

DOWNSHIFT to FAST if:
- Simple datetime request using time tool
- Direct search with obvious keywords
- Single-step action with clear tool choice

Examples:
switch_to: "fast", switch_why: "Query simplified to direct search"
switch_to: "fast", switch_why: "Single tool execution sufficient"
"""
