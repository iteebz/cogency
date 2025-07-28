"""Unified reasoning prompt with mode-specific injection."""


def prompt_unified_mode(
    mode: str,
    tool_registry: str,
    query: str,
    context: str,
    iteration: int = 0,
    max_iterations: int = 5,
    current_approach: str = "initial",
) -> str:
    """Generate unified prompt with mode-specific sections injected."""
    from cogency.constants import MAX_TOOL_CALLS_PER_ITERATION

    # Mode-specific reasoning instructions
    if mode == "deep":
        reasoning_phases = """
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

DOWNSHIFT to FAST if:
- Simple datetime request using time tool
- Direct search with obvious keywords
- Single-step action with clear tool choice

Examples:
switch_to: "fast", switch_why: "Query simplified to direct search"
switch_to: "fast", switch_why: "Single tool execution sufficient"
"""
        
        mode_context = f"""
CONTEXT:
Iteration {iteration}/{max_iterations} - Review completed actions to avoid repetition
Current approach: {current_approach}

PREVIOUS ACTIONS:
{context}
"""
    else:  # fast mode
        reasoning_phases = """
CRITICAL STOP CONDITIONS:
- If you see previous attempts that ALREADY answered the query → tool_calls: []
- If query is fully satisfied by previous results → tool_calls: []  
- If no tool can help with this query → tool_calls: []
- If repeating same failed action → tool_calls: []

GUIDANCE:
- FIRST: Review previous attempts to avoid repeating actions
- Use tools only if query needs MORE information

ESCALATE to DEEP if encountering:
- Tool results conflict and need synthesis
- Multi-step reasoning chains required  
- Ambiguous requirements need breakdown
- Complex analysis beyond direct execution

Examples:
switch_to: "deep", switch_why: "Search results contradict, need analysis"
switch_to: "deep", switch_why: "Multi-step calculation required"
"""
        
        mode_context = f"""
PREVIOUS CONTEXT:
{context if context else "Initial execution - no prior actions"}
"""

    return f"""
{mode.upper()}: {"Structured reasoning" if mode == "deep" else "Direct execution"} for query: {query}

CRITICAL: Output ONE JSON object for THIS ITERATION ONLY. Do not anticipate future steps.

JSON Response Format:
{{
  "thinking": "What am I trying to accomplish? What's my approach to this problem?",{
  '"reflect": "What worked/failed in previous actions? What gaps remain?",' if mode == "deep" else ""}{
  '"plan": "What specific tools to use next and expected outcomes?",' if mode == "deep" else ""}
  "tool_calls": [
    {{"name": "tool_a", "args": {{"param": "value"}}}},
    {{"name": "tool_b", "args": {{"param": "value"}}}},
    {{"name": "tool_c", "args": {{"param": "value"}}}}
  ],
  "switch_to": null,
  "switch_why": null,
  "summary_update": {{
    "goal": "What is the main objective?",
    "progress": "What has been accomplished so far?",
    "current_approach": "What strategy are we using?",
    "key_findings": "What important information have we discovered?",
    "next_focus": "What should be the next priority?"
  }}
}}

IMPORTANT: All {MAX_TOOL_CALLS_PER_ITERATION} tool calls must be in ONE tool_calls array, not separate JSON objects.

When done: {{"thinking": "explanation", "tool_calls": [], "switch_to": null, "switch_why": null, "summary_update": {{"goal": "updated goal", "progress": "final progress", "current_approach": "approach used", "key_findings": "what was learned", "next_focus": "none - complete"}}}}

TOOLS:
{tool_registry}

{mode_context}

{reasoning_phases}

- Empty tool_calls array ([ ]) if query fully answered or no progress possible
- If original query has been fully resolved, say so explicitly and return tool_calls: []
- LIMIT: Maximum {MAX_TOOL_CALLS_PER_ITERATION} tool calls per iteration to avoid JSON parsing issues
"""