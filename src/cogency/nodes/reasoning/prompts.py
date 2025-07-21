"""Centralized prompts for adaptive reasoning system."""

# Legacy prompt - kept for compatibility
REASON_PROMPT = """COGNITIVE CONTEXT:
Iteration: {current_iteration}/{max_iterations}
Current Strategy: {current_strategy}
Previous Attempts: {previous_attempts}
Last Tool Quality: {last_tool_quality}

ORIGINAL QUERY: {user_input}
AVAILABLE TOOLS: {tool_names}

REASONING FRAMEWORK:
Goal: [What am I trying to achieve?]
Last Step: [What did I just do?]
Finding: [What did I learn from the last action?]
Reflection: [Is my current strategy working? Should I adapt?]
Strategy: [What approach am I taking? e.g. direct_search, alternative_approach, synthesis]
New Step: [What should I do next?]

CRITICAL RULES:
1. If the user asks you to CREATE, RUN, EXECUTE, or SAVE anything - you MUST use tools
2. If the user wants files created or code executed - you MUST use appropriate tools
3. Only respond directly if the user asks for explanations or information you already know
4. FOLLOW TOOL SCHEMAS EXACTLY - include all required parameters
5. Adapt strategy if previous attempts failed or yielded poor results
6. Avoid repeating identical actions that already failed

STRATEGY ADAPTATION:
- If search failed: Try different keywords, broader/narrower scope, or different approach
- If tools failed: Check parameters, try alternative tools, or simplify request
- If stuck in loop: Break pattern with new strategy or direct response

RESPONSE FORMAT - YOU MUST OUTPUT EXACTLY THIS JSON FORMAT:

For CREATE/RUN/EXECUTE requests:
{{"reasoning": "Goal: [clear objective]. Strategy: [approach]. Action: [specific next step]", "strategy": "strategy_name", "tool_calls": [{{"name": "tool_name", "args": {{"param": "value"}}}}]}}

For information-only requests:
{{"reasoning": "Goal: [clear objective]. Assessment: I have sufficient information to respond directly.", "strategy": "direct_response"}}

CRITICAL: Output ONLY the JSON object. No explanations, no code blocks, no markdown."""


def get_fast_react_prompt(tool_info: str, current_input: str) -> str:
    """Pure ReAct prompt for fast mode - efficient direct execution."""
    return f"""QUERY: {current_input}
TOOLS: {tool_info}

ReAct fast: think → act → observe. Use tools if needed.

Escalate if complex: "switch_to": "deep", "switch_reason": "why"

JSON: {{"reasoning": "brief", "strategy": "approach", "switch_to": null|"deep", "switch_reason": null|"why"}}"""


def get_mode_switch_addition(mode: str) -> str:
    """Get mode switch prompt addition based on current mode."""
    if mode == "fast":
        return '\nEscalate if complex: "switch_to": "deep"'
    else:  # deep mode
        return '\nDownshift if simple: "switch_to": "fast"'


def build_reasoning_prompt(
    react_mode: str,
    current_iteration: int,
    tool_info: str,
    current_input: str,
    max_iterations: int,
    cognitive_state: dict,
    attempts_summary: str
) -> str:
    """Build adaptive reasoning prompt based on mode."""
    from cogency.nodes.reasoning.reflection import get_deep_reflection_prompt, should_use_reflection
    
    if react_mode == "deep" and should_use_reflection("deep", current_iteration):
        # Deep react: UltraThink-style reflection + planning + execution
        try:
            return get_deep_reflection_prompt(
                tool_info,
                current_input,
                current_iteration + 1,
                max_iterations,
                cognitive_state.get("current_strategy", "initial_approach"),
                attempts_summary,
                cognitive_state.get("last_tool_quality", "unknown")
            )
        except Exception:
            # Fallback to legacy deep reasoning
            return REASON_PROMPT.format(
                tool_names=tool_info,
                user_input=current_input,
                current_iteration=current_iteration + 1,
                max_iterations=max_iterations,
                current_strategy=cognitive_state.get("current_strategy", "initial_approach"),
                previous_attempts=attempts_summary,
                last_tool_quality=cognitive_state.get("last_tool_quality", "unknown")
            ) + get_mode_switch_addition("deep")
    else:
        # Fast react: Pure ReAct with switching capability
        return get_fast_react_prompt(tool_info, current_input) + get_mode_switch_addition("fast")