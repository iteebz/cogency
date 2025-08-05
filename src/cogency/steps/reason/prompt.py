"""Prompt building for reasoning - mode-specific prompt generation."""

from typing import Any, Dict, Optional

from cogency.state import AgentState

CORE_REASONING_INSTRUCTIONS = (
    """CRITICAL: Output ONE JSON object for THIS ITERATION ONLY. Do not anticipate future steps."""
)


def _build_json_format_section(mode: str) -> str:
    """Build JSON response format with mode-specific fields."""
    reflect_field = (
        '"reflect": "What worked/failed in previous actions? What gaps remain?",'
        if mode == "deep"
        else ""
    )
    plan_field = (
        '"plan": "What specific tools to use next and expected outcomes?",'
        if mode == "deep"
        else ""
    )

    return f"""{{
  "thinking": "What am I trying to accomplish? What's my approach to this problem?",{reflect_field}{plan_field}

  "tool_calls": [
    {{"name": "tool_a", "args": {{"arg": "value"}}}},
    {{"name": "tool_b", "args": {{"arg": "value"}}}},
    {{"name": "tool_c", "args": {{"arg": "value"}}}}
  ],
  "response": "Only populate this when ready to respond to the user directly",
  "switch_to": null,
  "switch_why": null,
  "workspace_update": {{
    "objective": "Clear problem statement: What is the main goal?",
    "assessment": "Current situation: What information have we gathered?",
    "approach": "Current strategy: What method are we using?",
    "observations": "Key findings: What important insights have we found?"
  }}
}}"""


WORKSPACE_UPDATE_GUIDELINES = """WORKSPACE UPDATE FIELDS:
- objective: Clear problem statement - what are we trying to achieve?
- assessment: Current situation - what facts/context do we have?
- approach: Strategy being used - how are we solving this?
- observations: Key insights - what important findings have emerged?"""


def _build_tool_execution_guidelines(max_tool_calls: int) -> str:
    """Build tool execution guidelines."""
    return f"""CRITICAL DECISION LOGIC:
- If user requests tool usage (shell commands, file operations, etc.) → Use tool_calls array, leave response empty
- If you can answer directly without tools → Use response field, leave tool_calls empty
- NEVER put tool descriptions in response field when user requested tool execution

TOOL EXECUTION: All {max_tool_calls} tool calls must be in ONE tool_calls array, not separate JSON objects.

When using tools: {{"thinking": "I need to execute tools", "tool_calls": [{{"name": "shell", "args": {{"command": "echo hello"}}}}], "response": "", "switch_to": null, "switch_why": null, "workspace_update": {{...}}}}

When ready to respond: {{"thinking": "explanation", "security_assessment": {{"risk_level": "SAFE", "threats_detected": [], "restrictions": [], "reasoning": "No security risks detected"}}, "tool_calls": [], "response": "your response to the user", "switch_to": null, "switch_why": null, "workspace_update": {{"objective": "updated objective", "assessment": "what we learned", "approach": "approach used", "observations": "key insights found"}}}}"""


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


def _build_deep_downshift_rules(max_iterations: int) -> str:
    """Build downshift rules for deep mode."""
    return f"""DOWNSHIFT to FAST if:
- Simple datetime request using time tool
- Direct search with obvious keywords
- Single-step action with clear tool choice
- Approaching max_iterations limit ({max_iterations} iterations) - prioritize direct execution
- Complex analysis not yielding progress after 2+ iterations

Examples:
switch_to: "fast", switch_why: "Query simplified to direct search"
switch_to: "fast", switch_why: "Single tool execution sufficient"
switch_to: "fast", switch_why: "Approaching max_iterations limit, need direct action\""""


FAST_REASONING_STEPS = """CRITICAL STOP CONDITIONS:
- If you see previous attempts that ALREADY answered the query → populate "response"
- If query is fully satisfied by previous results → populate "response"  
- If no tool can help with this query → populate "response"
- If repeating same failed action → populate "response"

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
switch_to: "deep", switch_why: "Multi-step calculation required\""""


FINAL_EXECUTION_GUIDELINES = """- Populate "response" field when ready to respond directly to the user
- If original query has been fully resolved, populate "response" with your answer
- LIMIT: Maximum {max_tool_calls} tool calls per iteration to avoid JSON parsing issues"""


class Prompt:
    """Builds reasoning prompts with mode-specific logic."""

    def build(
        self,
        mode: str,
        query: str,
        context_data: Dict[str, Any],
        iteration: int,
        max_iterations: int,
        state: AgentState,
        identity: Optional[str] = None,
    ) -> str:
        """Build reasoning prompt with mode-specific sections."""
        from cogency.config import MAX_TOOL_CALLS

        # Get context components
        tool_registry = context_data["tool_registry"]
        reasoning_context = context_data["reasoning_context"]
        memory_context = context_data["memory_context"]
        workspace_context = context_data["workspace_context"]

        # Build mode-specific context
        if mode == "deep":
            reasoning_steps = self._build_deep_steps(max_iterations)
            mode_context = self._build_deep_context(
                iteration, max_iterations, memory_context, workspace_context, reasoning_context
            )
        else:  # fast mode
            reasoning_steps = self._build_fast_steps()
            mode_context = self._build_fast_context(
                memory_context, workspace_context, reasoning_context
            )

        # Build base prompt using decomposed sections
        prompt = f"""
{mode.upper()}: {"Structured reasoning" if mode == "deep" else "Direct execution"} for query: {query}

{CORE_REASONING_INSTRUCTIONS}

{_build_tool_execution_guidelines(MAX_TOOL_CALLS)}

{WORKSPACE_UPDATE_GUIDELINES}

TOOLS:
{tool_registry}

{mode_context}

{reasoning_steps}

{FINAL_EXECUTION_GUIDELINES.format(max_tool_calls=MAX_TOOL_CALLS)}

JSON Response Format:
{_build_json_format_section(mode)}
"""

        # Add identity if provided
        if identity:
            prompt = f"{identity}\n\n{prompt}"

        return prompt

    def _build_deep_steps(self, max_iterations: int) -> str:
        """Build deep reasoning step instructions."""
        return f"""
{DEEP_REASONING_STEPS}

{_build_deep_downshift_rules(max_iterations)}
"""

    def _build_fast_steps(self) -> str:
        """Build fast reasoning step instructions."""
        return f"""
{FAST_REASONING_STEPS}
"""

    def _build_deep_context(
        self,
        iteration: int,
        max_iterations: int,
        memory_context: str,
        workspace_context: str,
        reasoning_context: str,
    ) -> str:
        """Build deep mode context section."""
        return f"""
CONTEXT:
Iteration {iteration}/{max_iterations} - Review completed actions to avoid repetition

{memory_context}COGNITIVE WORKSPACE:
{workspace_context}

PREVIOUS ACTIONS:
{reasoning_context}
"""

    def _build_fast_context(
        self, memory_context: str, workspace_context: str, reasoning_context: str
    ) -> str:
        """Build fast mode context section."""
        return f"""
{memory_context}COGNITIVE WORKSPACE:
{workspace_context}

PREVIOUS CONTEXT:
{reasoning_context if reasoning_context else "Initial execution - no prior actions"}
"""
