"""Centralized reasoning prompts for ReAct workflow."""

from cogency.constants import ReasoningActions


class ReasoningPrompts:
    """Collection of prompts for reasoning workflow."""
    
    INITIAL_REASON = """You are in a ReAct reasoning loop. Analyze the current situation and decide your next action.

CONTEXT: Look at the conversation history and any tool results from previous actions.
GOAL: {user_input}

Available tools: {tool_names}

Based on what you know so far, decide:
1. Do you have enough information to provide a complete answer? 
2. Or do you need to gather more information using tools?

First, explain your reasoning in a clear, concise way (1-2 sentences). Then provide your decision in JSON format.

REASONING: [Your step-by-step thinking about what you need to do]

JSON_DECISION:
- If you can answer completely: {{"action": "respond", "answer": "your complete answer"}}
- If you need one tool: {{"action": "use_tool", "tool_call": {{"name": "tool_name", "args": {{"param": "value"}}}}}}
- If you need multiple tools: {{"action": "use_tools", "tool_call": {{"calls": [{{"name": "tool1", "args": {{"param": "value"}}}}, {{"name": "tool2", "args": {{"param": "value"}}}}]}}}}"""

    REFLECTION = """You are in a ReAct reasoning loop. You just received tool results - reflect on them and decide your next action.

GOAL: {user_input}
Available tools: {tool_names}

REFLECTION QUESTIONS:
1. Did the tool results help answer the user's question?
2. Are the results what you expected? Any errors or issues?
3. Do you need more information or can you provide a complete answer now?
4. If you need more info, what specific tools should you use next?

First, explain your reflection on the tool results (1-2 sentences). Then provide your decision in JSON format.

REASONING: [Your reflection on the tool results and next steps]

JSON_DECISION:
- If you can answer completely: {{"action": "respond", "answer": "your complete answer"}}
- If you need one tool: {{"action": "use_tool", "tool_call": {{"name": "tool_name", "args": {{"param": "value"}}}}}}
- If you need multiple tools: {{"action": "use_tools", "tool_call": {{"calls": [{{"name": "tool1", "args": {{"param": "value"}}}}, {{"name": "tool2", "args": {{"param": "value"}}}}]}}}}"""

    FALLBACK_SUMMARY = """Based on all the tool results and analysis in the conversation, provide a comprehensive answer to the user's original question. 

Stopping reason: {stopping_reason}

Synthesize all the information gathered from tool executions into a clear, helpful response that directly addresses what the user asked for."""

    FALLBACK_SYSTEM = "Provide a clear, comprehensive summary based on all the tool results and reasoning shown in the conversation."