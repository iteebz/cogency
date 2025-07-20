"""Single unified reasoning prompt - no ceremony."""

UNIFIED_REASON = """Analyze the conversation and decide your next action.

QUERY: {user_input}
AVAILABLE TOOLS: {tool_names}

CRITICAL: Only use tools for current/external data. Answer simple questions directly with your knowledge.

Examples:
- "What is 2+2?" → Direct answer (no calculator needed)
- "Weather in Paris?" → Use weather tool
- "Current time in Tokyo?" → Use timezone tool

Review conversation history and any tool results, then decide:

{{"reasoning": "Explain your thinking in 1-2 sentences", "action": "respond"}}
OR
{{"reasoning": "Why you need this tool", "action": "use_tool", "tool_call": {{"name": "tool_name", "args": {{"param": "value"}}}}}}
OR  
{{"reasoning": "Why you need these tools", "action": "use_tools", "tool_call": {{"calls": [...]}}}}"""

FALLBACK_SUMMARY = """Based on all the tool results and analysis in the conversation, provide a comprehensive answer to the user's original question. 

Stopping reason: {stopping_reason}

Synthesize all the information gathered from tool executions into a clear, helpful response that directly addresses what the user asked for."""

FALLBACK_SYSTEM = "Provide a clear, comprehensive summary based on all the tool results and reasoning shown in the conversation."