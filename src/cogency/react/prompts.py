"""Prompts: ReAct prompt building and formatting."""

from ..context.assembly import inject_context


def build_prompt(task: str, user_id: str, tool_results: list[dict], tools: dict) -> str:
    """Build ReAct prompt with context, task, tools, and history."""
    # Inject context for this user and task with working memory
    context = inject_context(task, user_id, tool_results)

    # Available tools
    tool_descriptions = []
    for tool in tools.values():
        tool_descriptions.append(f"- {tool.name}: {tool.description}")

    tools_text = "\n".join(tool_descriptions)

    # Recent tool results (last 3)
    if tool_results:
        results_text = "PREVIOUS TOOL RESULTS:\n"
        for result in tool_results[-3:]:
            tool_name = result["tool"]
            if "result" in result:
                results_text += f"✅ {tool_name}: {str(result['result'])[:200]}...\n"
            else:
                results_text += f"❌ {tool_name}: {str(result.get('error', 'Unknown error'))}\n"
    else:
        results_text = "No previous tool results."

    # Build full prompt with context
    prompt_parts = []

    if context.strip():
        prompt_parts.append(f"CONTEXT:\n{context}")

    prompt_parts.extend([f"TASK: {task}", f"AVAILABLE TOOLS:\n{tools_text}", results_text])

    full_context = "\n\n".join(prompt_parts)

    return f"""{full_context}

Your response MUST be valid JSON with this structure:
{{
  "reasoning": "Your step-by-step thinking about what to do next",
  "action": {{
    "type": "tool_call",
    "name": "tool_name",
    "args": {{"arg1": "value1", "arg2": "value2"}},
    "rationale": "Why you're using this tool"
  }}
}}

OR when the task is COMPLETE:
{{
  "reasoning": "Summary of what you accomplished and why the task is complete",
  "final_answer": "Task completed successfully. [Brief summary of what was done]",
  "action": {{"type": "final_answer"}}
}}

IMPORTANT: When the task is fully completed, you MUST use the final_answer format.
Respond with JSON only, no other text."""
