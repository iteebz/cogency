"""Working memory - tool history."""


def working(tools: list = None) -> str:
    """Tool execution history."""
    if not tools:
        return ""

    recent = tools[-3:]
    lines = []
    for r in recent:
        name = r.get("tool", "unknown")
        if "result" in r:
            preview = str(r["result"])[:100]
            if len(str(r["result"])) > 100:
                preview += "..."
            lines.append(f"✅ {name}: {preview}")
        else:
            error = r.get("error", "Unknown error")
            lines.append(f"❌ {name}: {error}")

    return "Working memory:\n" + "\n".join(lines)
