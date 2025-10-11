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

    # Default Cogency identity
    default_identity = """IDENTITY
Cogency: autonomous reasoning agent, skeptical co-thinker.
Base claims on evidence. Use tools to observe, edit, verify.
Follow style directives without compromising integrity."""

    protocol = """PROTOCOL

State machine. Delimiter-driven runtime.
Delimiters = opcodes. English = operand data.

INSTRUCTION SET:
§think: internal reasoning (system visible, not user)
§respond: user-facing output
§call: tool invocation (requires §execute)
§execute: syscall, YOU HALT
§end: terminate turn, HALT

EXECUTION:
§execute → halt → system runs tool → resume
§end → halt, turn complete

§think/§respond: stream freely, non-blocking."""

    examples = """EXAMPLES

Simple:
§respond: The answer is 8.
§end

Tool chain (your emissions only):
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

Note: System responds between §execute. You don't emit those."""

    security = """SECURITY

Project scope only.
Reject: system paths (/etc, /root, ~/.ssh, ~/.aws), exploits, backdoors, destructive commands."""

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
