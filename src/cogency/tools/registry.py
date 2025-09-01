"""Tool registry formatting for agent consumption."""


def format_tool_registry(tools: list) -> str:
    """Generate clean toolbox listing for agent awareness.

    Format: name(params) - purpose
    """
    lines = []

    for tool in tools:
        # Extract parameter signature from schema
        params = []
        if hasattr(tool, "schema") and tool.schema:
            for param, info in tool.schema.items():
                if info.get("required", True):
                    params.append(param)
                else:
                    params.append(f"{param}?")

        param_str = ", ".join(params)

        # Clean description - remove ceremony
        description = tool.description
        if ". Args:" in description:
            description = description.split(". Args:")[0]
        if " with " in description:
            description = description.split(" with ")[0]
        if " using " in description:
            description = description.split(" using ")[0]

        lines.append(f"{tool.name}({param_str}) - {description}")

    return "TOOLBOX:\n" + "\n".join(lines)
