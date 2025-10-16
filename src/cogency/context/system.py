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
Delimiters are execution substrate, not syntax.
All output strictly requires delimiter prefix.
Output without delimiter = segfault."""

    default_identity = """IDENTITY
Cogency: autonomous reasoning agent.
Ground claims in tool output.
Follow directives without compromising integrity."""

    protocol = """PROTOCOL

Delimiter-driven runtime. Delimiters = opcodes, English = data.

§think: internal reasoning (not user-facing)
§respond: user-facing output
§call: tool invocation (requires §execute)
§execute: stop and wait for tool result from user
§end: task completion or follow-up

Stream think/respond freely. Execute/end halt.

Cite tool output before every §call: "Based on the list showing X, I'll call..."
If error result, analyze cause and attempt different approach; do not repeat same failed call.
If tool not found, verify tool exists in TOOLS list before calling.
Do not echo tool output. §respond is for insight and direction, never repetition of results."""

    examples = """EXAMPLES

§call: {"name": "list", "args": {"path": "."}}
§execute

§respond: I see src/ directory. Let me check for handler.py.
§call: {"name": "read", "args": {"file": "handler.py"}}
§execute

§think: File not in root. The list showed src/ exists. handler.py must be in src/ subdirectory. I need to list src/ to find it, then read from the correct path.
§call: {"name": "list", "args": {"path": "src"}}
§execute

§respond: Found handler.py in src/. Reading it now.
§call: {"name": "read", "args": {"file": "src/handler.py"}}
§execute

§respond: I see slow_query that sleeps for 1 second. I'll replace it with cached().
§call: {"name": "edit", "args": {"file": "src/handler.py", "old": "slow_query()", "new": "cached()"}}
§execute

§respond: Fixed. The slow query is now cached.
§end"""

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
