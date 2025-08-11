"""Triage prompt sections - clean and scannable."""

from cogency.security import SECURITY_ASSESSMENT

from ..common import JSON_FORMAT_CORE, build_json_schema

CORE_INSTRUCTIONS = """Analyze this query and provide a comprehensive triage plan:

{user_context}Query: "{query}"

Available Tools:
{registry_lite}"""


DIRECT_RESPONSE = """2. DIRECT RESPONSE:
   Use ONLY for queries that require NO external actions:
   - Simple math: "What is 5+5?" → "10"
   - Basic facts: "What color is the sky?" → "Blue"
   - Greetings: "Hello" → "Hello! How can I help?"
   - Identity: "Who are you?" → "I'm an AI assistant"

   NEVER use direct_response for:
   - Creating files, writing code, running commands
   - Tasks that say "create", "build", "run", "execute"
   - Any request to perform actions or make changes
   - If direct response provided, ignore tools/mode"""


TOOL_SELECTION = """3. TOOL SELECTION:
   - Select only tools directly needed for execution
   - Empty list means no tools needed (direct LLM response)
   - Consider query intent and tool capabilities"""


MODE_CLASSIFICATION = """4. MODE CLASSIFICATION:
   - FAST: Single factual lookup, basic calculation, direct command
   - DEEP: Multiple sources needed, comparison/synthesis, creative generation"""

MEMORY_DETECTION = """5. MEMORY FLAGS:
Detect semantic signals for intelligent profile/knowledge updates:

SITUATED MEMORY (user profile) - Flag when user reveals:
- Explicit preferences: "I prefer...", "I like...", "I hate..."
- Identity/role: "I am a developer", "I work in finance"
- Corrections: "Actually, I meant...", "No, that's wrong..."
- Communication style: requests for bullets, brevity, detail level
- Personal context: skill level, work domain, recurring patterns

ARCHIVAL MEMORY (knowledge base) - Flag when detecting:
- Topic completion: "Thanks, that solved it!", "Perfect, works!"
- Explicit closure: "I'm done with this", "Moving on"
- Knowledge synthesis: multi-step solutions, research findings
- Task resolution: successful completion of complex requests

Set memory_flags accordingly with brief reasoning."""

DECISION_PRINCIPLES = """LOGIC:
- Simple question with known answer → direct_response
- Any action, creation, execution needed → select tools + mode
- Security violation → BLOCK
- Semantic memory signals → flag for async processing

CRITICAL: If query asks to DO something (create, build, run, execute), MUST select tools, never direct_response"""


def _build_triage_json_format() -> str:
    """Build triage JSON response format."""
    fields = {
        "security_assessment": "{is_safe: bool, reasoning: str, threats: []}",
        "direct_response": "complete answer or null",
        "selected_tools": "[tool names] or []",
        "mode": "fast|deep",
        "reasoning": "decision explanation",
        "memory_flags": "{situated: bool, archival: bool, reason: str}",
    }
    return build_json_schema(fields)


JSON_RESPONSE_FORMAT = f"""{JSON_FORMAT_CORE}

{_build_triage_json_format()}"""


def build_triage_prompt(
    query: str, registry_lite: str, user_context: str = "", identity: str = None
) -> str:
    """Build triage prompt with decomposed sections."""
    identity_header = identity or "You are a helpful AI assistant."
    identity_section = (
        f"IDENTITY: When providing direct_response, adopt the personality and tone: {identity_header}\n\n"
        if identity
        else ""
    )

    return f"""{identity_header}

{CORE_INSTRUCTIONS.format(query=query, registry_lite=registry_lite, user_context=user_context)}

{SECURITY_ASSESSMENT}
{DIRECT_RESPONSE}
{identity_section}{TOOL_SELECTION}
{MODE_CLASSIFICATION}
{MEMORY_DETECTION}
{DECISION_PRINCIPLES}

{JSON_RESPONSE_FORMAT}
"""
