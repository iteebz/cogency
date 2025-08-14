"""Working: Current task working memory - tool history and progress."""


def working(tool_results: list = None) -> str:
    """Current task working memory - tool history and progress."""
    if not tool_results:
        return ""

    # Format recent tool executions for context (last 3)
    recent = tool_results[-3:]
    formatted = []
    for result in recent:
        tool_name = result.get("tool", "unknown")
        if "result" in result:
            preview = str(result["result"])[:100]
            if len(str(result["result"])) > 100:
                preview += "..."
            formatted.append(f"✅ {tool_name}: {preview}")
        else:
            error = result.get("error", "Unknown error")
            formatted.append(f"❌ {tool_name}: {error}")

    return "Working memory:\n" + "\n".join(formatted)
