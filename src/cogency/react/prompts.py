"""ReAct prompt building."""

from ..context.assembly import context


def prompt(task: str, user_id: str, tool_results: list[dict], tools: dict) -> str:
    """Build ReAct prompt."""
    ctx = context(task, user_id, tool_results)

    tools_text = "\n".join(f"- {t.name}: {t.description}" for t in tools.values())

    if tool_results:
        results_text = "PREVIOUS TOOLS:\n"
        for r in tool_results[-3:]:
            name = r["tool"]
            if "result" in r:
                results_text += f"✅ {name}: {str(r['result'])[:200]}...\n"
            else:
                results_text += f"❌ {name}: {str(r.get('error', 'Unknown error'))}\n"
    else:
        results_text = ""

    parts = []
    if ctx.strip():
        parts.append(ctx)

    parts.append(f"TASK: {task}")

    if tools:
        parts.append(f"TOOLS:\n{tools_text}")

    if results_text:
        parts.append(results_text)

    prompt = "\n\n".join(parts)

    return f"""{prompt}

Think step by step. Use tools when needed by writing:
USE: tool_name(arg1="value1", arg2="value2")

When complete, write your final answer."""
