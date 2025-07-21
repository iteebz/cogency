"""Reasoning prompts and templates."""

# ENHANCED REASON PROMPT - Structured cognitive reasoning with adaptive strategy
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