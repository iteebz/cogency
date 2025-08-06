"""Prompt building for reasoning - mode-specific prompt generation."""

from typing import Any, List, Optional

from cogency.state import AgentState

from ..common import JSON_FORMAT_CORE, TOOL_RESPONSE_LOGIC, build_json_schema

CORE_REASONING_INSTRUCTIONS = f"""CRITICAL: {JSON_FORMAT_CORE}

EXAMPLE FOR SIMPLE QUERY "what was my last message?":
{{"thinking": "Checking conversation history", "tool_calls": [], "response": "hi there"}}

EXAMPLE FOR COMPLEX TASK:
{{"thinking": "Need to search for current information", "tool_calls": [{{"name": "search", "args": {{"query": "..."}}}}], "response": ""}}

NEVER OUTPUT:
```json
- yaml format
plain text reasoning"""


def _build_json_format_section(mode: str) -> str:
    """Build JSON response format with mode-specific fields."""
    fields = {
        "thinking": "Brief reasoning for this step (shown to user)",
        "tool_calls": '[{"name": "tool", "args": {}}] or []',
        "workspace_update": "{objective, assessment, approach, observations}",
        "response": "clean direct answer (REQUIRED if tool_calls=[]) or empty string",
        "switch_to": "fast|deep (optional)",
        "switch_why": "reason for mode switch (if switching)",
    }
    return build_json_schema(fields)


WORKSPACE_UPDATE_GUIDELINES = """WORKSPACE UPDATE FIELDS:
- objective: Clear problem statement - what are we trying to achieve?
- assessment: Current situation - what facts/context do we have?
- approach: Strategy being used - how are we solving this?
- observations: Key insights - what important findings have emerged?"""


def _build_tool_execution_guidelines(max_tool_calls: int) -> str:
    """Build tool execution guidelines."""
    return f"""{TOOL_RESPONSE_LOGIC}

TOOL MODE: Actions needed → tool_calls=[...], response=""
RESPONSE MODE: Task complete → tool_calls=[], response="answer"

Limit: Max {max_tool_calls} tools per iteration for JSON stability."""


DEEP_REASONING_STEPS = """REASONING STEPS:
🤔 REFLECT: Review completed actions and their DETAILED results - what information do you already have? What gaps remain?
📋 PLAN: Choose NEW tools that address remaining gaps - avoid repeating successful actions
🎯 EXECUTE: Run planned tools sequentially when they address different aspects

RECOVERY ACTIONS:
- Tool argument errors → Check required vs optional args in schema
- No results from tools → Try different args or alternative approaches
- Information conflicts → Use additional tools to verify or synthesize  
- Use the DETAILED action history to understand what actually happened, not just success/failure
- Avoid repeating successful tool calls - check action history first"""


FAST_REASONING_STEPS = """GUIDANCE:
- FIRST: Review previous attempts to avoid repeating actions
- Use tools when you need to take actions or gather information
- Only provide "response" when you have FULLY completed the user's request

ESCALATE to DEEP if encountering:
- Tool results conflict and need synthesis
- Multi-step reasoning chains required  
- Ambiguous requirements need breakdown
- Complex analysis beyond direct execution

Examples:
switch_to: "deep", switch_why: "Search results contradict, need analysis"
switch_to: "deep", switch_why: "Multi-step calculation required\""""


FINAL_EXECUTION_GUIDELINES = """COMPLETION DECISION:
When to CONTINUE: tool_calls=[...], response=""
- Need more information to answer completely
- Haven't addressed all parts of the query

When to COMPLETE: tool_calls=[], response="clean direct answer"
- Have sufficient information to provide complete answer
- All query requirements satisfied
- CRITICAL: If you have taken multiple actions and made progress, you MUST complete with a summary
- NEVER generate tool_calls=[] with response="" - this causes infinite loops

RESPONSE GUIDELINES:
- "thinking": Brief process explanation (user sees this)
- "response": Clean, direct answer only (user's final result)
- Keep thinking concise - avoid repeating response content  
- For simple queries, thinking should be brief decision, response should be the actual answer
- IDENTITY: When providing "response", adopt the personality and tone described in the system prompt above

Max {max_tool_calls} tools/iteration for stability."""


class Prompt:
    """Builds reasoning prompts with mode-specific logic."""

    def build(
        self,
        state: AgentState,
        tools: List[Any],
        mode: Optional[str] = None,
        identity: Optional[str] = None,
    ) -> str:
        """Build reasoning prompt with mode-specific sections."""
        from cogency.config import MAX_TOOL_CALLS
        from cogency.state.context import (
            execution_history,
            knowledge_synthesis,
            readiness_assessment,
        )
        from cogency.tools.registry import build_tool_schemas

        mode = mode or state.execution.mode
        mode_value = mode.value if hasattr(mode, "value") else str(mode)

        # Get context fragments from state/context.py
        user_context = state.get_situated_context()
        reasoning_context = state.reasoning.compress_for_context()
        execution_context = execution_history(state, tools)
        knowledge_context = knowledge_synthesis(state)
        readiness_context = readiness_assessment(state)

        # Tool registry
        if tools:
            tool_registry = build_tool_schemas(tools)
            tools_section = f"AVAILABLE TOOLS:\n{tool_registry}"
        else:
            tools_section = "NO TOOLS AVAILABLE - You can only provide direct responses"

        # Build mode-specific instructions with centralized switching guidelines
        from .modes import ModeController

        if mode_value == "deep":
            instructions = f"""DEEP MODE: Structured reasoning required
- REFLECT: What have I learned? What worked/failed? What gaps remain?
- ANALYZE: What are the core problems or strategic considerations?  
- STRATEGIZE: What's my multi-step plan? What tools will I use and why?
- WORKSPACE: Update goal, strategy, and insights for structured reflection

{ModeController.get_switch_guidelines("deep", state.execution.max_iterations)}"""
        elif mode_value == "adapt":
            instructions = f"""ADAPT MODE: Dynamic reasoning - start fast, escalate as needed
- Review context above
- Choose appropriate tools and act efficiently
- ESCALATE to deep mode when encountering complexity

{ModeController.get_switch_guidelines("adapt", state.execution.max_iterations)}"""
        else:
            instructions = f"""FAST MODE: Direct execution
- Review context above
- Choose appropriate tools and act efficiently
- Focus on immediate action completion

{ModeController.get_switch_guidelines("fast", state.execution.max_iterations)}"""

        # Build complete prompt
        identity_header = identity or "You are a helpful AI assistant."

        prompt = f"""{identity_header}

{user_context}REASONING CONTEXT:
{reasoning_context}

{execution_context}{knowledge_context}{readiness_context}{tools_section}

{instructions}

Iteration {state.execution.iteration}/{state.execution.max_iterations}

{CORE_REASONING_INSTRUCTIONS}

{_build_tool_execution_guidelines(MAX_TOOL_CALLS)}

{WORKSPACE_UPDATE_GUIDELINES}

{FINAL_EXECUTION_GUIDELINES.format(max_tool_calls=MAX_TOOL_CALLS)}

JSON Response Format:
{_build_json_format_section(mode_value)}
"""

        return prompt
