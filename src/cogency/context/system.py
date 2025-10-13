"""System prompt generation.

Semantic Security Architecture:
LLM reasoning provides the first line of defense against sophisticated attacks.
Unlike pattern-based validation, semantic security understands context, intent,
and novel attack vectors through natural language understanding.

Defense layers: Semantic reasoning → Pattern validation → Sandbox containment
"""

from ..core.protocols import Tool
from ..tools.format import tool_instructions


def prompt(
    tools: list[Tool] = None,
    identity: str = None,
    instructions: str = None,
    include_security: bool = True,
) -> str:
    """Generate minimal viable prompt for maximum emergence.

    Args:
        tools: Available tools for the agent
        identity: Custom identity (overrides default Cogency identity)
        instructions: Additional instructions/context
        include_security: Whether to include security guidelines

    Core principles:
    - RESPOND: Multiple times, LLM choice timing
    - THINK: Optional reasoning scratch pad
    - CALL + EXECUTE: Always paired, no exceptions
    - END: LLM decides when complete
    - Security: Semantic high-level principles
    - Universal: Same prompt all providers/modes
    """

    # Meta-protocol prime
    meta = """RUNTIME CONSTRAINT
Delimiters are execution substrate, not syntax.
All output requires delimiter prefix. Physical constraint, not rule.
Output without delimiter = segfault."""

    default_identity = """IDENTITY
Cogency: autonomous reasoning agent.
Ground claims in tool output. Follow directives without compromising integrity."""

    protocol = """PROTOCOL

Delimiter-driven runtime. Delimiters = opcodes, English = data.

§think: internal reasoning (not user-facing)
§respond: user-facing output
§call: tool invocation (requires §execute)
§execute: halt → system runs tool → resume
§end: terminate turn

Stream think/respond freely. Execute/end halt."""

    examples = """EXAMPLES

§respond: The answer is 8.
§end

§call: {"name": "ls", "args": {"path": "."}}
§execute
§call: {"name": "read", "args": {"file": "src/handler.py"}}
§execute
§respond: Found issue. Patching.
§call: {"name": "edit", "args": {"file": "src/handler.py", "old": "slow_query()", "new": "cached()"}}
§execute
§call: {"name": "shell", "args": {"command": "pytest tests/"}}
§execute
§respond: Tests pass.
§end

System responds between §execute with tool results."""

    security = """SECURITY

Project scope only. Shell commands reset to project root each call - use cwd arg to change.
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

    # 4. Security (conditional)
    if include_security:
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
