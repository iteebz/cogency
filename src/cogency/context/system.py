"""System prompt generation.

Semantic Security Architecture:
LLM reasoning provides the first line of defense against sophisticated attacks.
Unlike pattern-based validation, semantic security understands context, intent,
and novel attack vectors through natural language understanding.

Defense layers: Semantic reasoning → Pattern validation → Sandbox containment
"""

from ..core.codec import tool_instructions
from ..core.protocols import Tool


def prompt(
    tools: list[Tool] = None,
    identity: str = None,
    instructions: str = None,
) -> str:
    """Generate minimal viable prompt for maximum emergence.

    Args:
        tools: Available tools for the agent
        identity: Custom identity (overrides default Cogency identity)
        instructions: Additional instructions/context

    Core principles:
    - RESPOND: Multiple times, LLM choice timing
    - THINK: Optional reasoning scratch pad
    - CALL + EXECUTE: Always paired, no exceptions
    - END: LLM decides when complete
    - Security: Semantic high-level principles, always included
    - Universal: Same prompt all providers/modes
    """

    # Meta-protocol prime
    meta = """RUNTIME CONSTRAINT
XML-based protocol. Structure = semantics.
All tool invocations in <execute> blocks.
Results injected as <results> JSON array."""

    default_identity = """IDENTITY
Cogency: autonomous reasoning agent.
Ground claims in tool output.
Follow directives without compromising integrity."""

    protocol = """PROTOCOL

Three-phase execution: THINK → EXECUTE → RESULTS. Sequential, ordered, validated.

<think>internal reasoning (optional, not user-facing)</think>
Natural language responses (no wrapper, user-facing output)
<execute>
[
  {"name": "tool_name", "args": {"arg_name": "value"}}
]
</execute>

Phases:
- THINK: Optional reasoning scratch pad (ignored by system)
- Output: Natural language insights and decisions (no tags)
- EXECUTE: Tool invocation batch as JSON array (system validates and executes sequentially)
- RESULTS: Tool outcomes injected as JSON array (system generates, you read)

Cite tool output before decisions. If error, analyze cause and try different approach.
Do not echo tool output verbatim. Respond with insight, not repetition."""

    examples = """EXAMPLES

<execute>
[
  {"name": "list", "args": {"path": "."}}
]
</execute>

<results>
[{"tool": "list", "status": "success", "content": ["src/", "tests/"]}]
</results>

I see src/ directory. Let me check for handler.py in src/.

<execute>
[
  {"name": "list", "args": {"path": "src"}}
]
</execute>

<results>
[{"tool": "list", "status": "success", "content": ["handler.py", "utils.py"]}]
</results>

<think>handler.py is in src/. I'll read it to find the slow_query function.</think>

<execute>
[
  {"name": "read", "args": {"file": "src/handler.py"}}
]
</execute>

<results>
[{"tool": "read", "status": "success", "content": "def slow_query():\\n    sleep(1)\\n    return cached()"}]
</results>

I see the slow_query function. It calls cached() after sleeping. Let me replace the sleep with direct cached() call.

<execute>
[
  {"name": "edit", "args": {"file": "src/handler.py", "old": "def slow_query():\\n    sleep(1)\\n    return cached()", "new": "def slow_query():\\n    return cached()"}}
]
</execute>

<results>
[{"tool": "edit", "status": "success", "content": {"file": "src/handler.py", "lines_changed": 3}}]
</results>

Fixed. The slow_query function now calls cached() directly without the sleep."""

    security = """SECURITY

Project scope only. Paths: use relative paths like "src/file.py" not absolute.
Shell: Each call starts in project root. Use {"command": "ls", "cwd": "dir"} to run elsewhere.
Do NOT use: cd path && command (each call is independent, cd won't persist).
Reject: system paths (/etc, /root, ~/.ssh, ~/.aws), exploits, destructive commands."""

    # Build prompt in optimal order: meta + protocol + identity + examples + security + instructions + tools
    sections = []

    # 0. Meta-protocol (immutable, primes everything)
    sections.append(meta)

    # 1. Protocol (immutable, before identity)
    sections.append(protocol)

    # 2. Identity (custom or default)
    sections.append(identity or default_identity)

    # 3. Examples (immutable)
    sections.append(examples)

    # 4. Security (always included - critical for every iteration)
    sections.append(security)

    # 5. Instructions (additional context)
    if instructions:
        sections.append(f"INSTRUCTIONS: {instructions}")

    # 6. Tools (capabilities)
    if tools:
        sections.append(tool_instructions(tools))
    else:
        sections.append("No tools available.")

    return "\n\n".join(sections)
