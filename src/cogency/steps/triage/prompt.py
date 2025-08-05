"""Triage prompt sections - clean and scannable."""

from cogency.security import SECURITY_ASSESSMENT

CORE_INSTRUCTIONS = """Analyze this query and provide a comprehensive triage plan:

Query: "{query}"

Available Tools:
{registry_lite}"""


DIRECT_RESPONSE = """2. DIRECT RESPONSE:
   - Simple math: "What is 5+5?" → "10"
   - Basic facts: "What color is the sky?" → "Blue"
   - Greetings: "Hello" → "Hello! How can I help?"
   - Identity: "Who are you?" → "I'm an AI assistant"
   - If direct response provided, ignore tools/mode"""


TOOL_SELECTION = """3. TOOL SELECTION:
   - Select only tools directly needed for execution
   - Empty list means no tools needed (direct LLM response)
   - Consider query intent and tool capabilities"""


MODE_CLASSIFICATION = """4. MODE CLASSIFICATION:
   - FAST: Single factual lookup, basic calculation, direct command
   - DEEP: Multiple sources needed, comparison/synthesis, creative generation"""


DECISION_PRINCIPLES = """LOGIC:
- Direct answer available → direct_response
- Tools needed → select tools + mode  
- Security violation → BLOCK"""


JSON_RESPONSE_FORMAT = """JSON Response:
{
  "security_assessment": {
    "is_safe": true | false,
    "reasoning": "brief explanation of security decision",
    "threats": ["specific threat types if any"]
  },
  "direct_response": "complete answer if query can be answered directly without tools" | null,
  "selected_tools": ["tool1", "tool2"] | [],
  "mode": "fast" | "deep",
  "reasoning": "brief explanation of decisions"
}"""


def build_triage_prompt(query: str, registry_lite: str) -> str:
    """Build triage prompt with decomposed sections."""
    return f"""{CORE_INSTRUCTIONS.format(query=query, registry_lite=registry_lite)}

DECISION RULES:

{SECURITY_ASSESSMENT}

{DIRECT_RESPONSE}

{TOOL_SELECTION}

{MODE_CLASSIFICATION}

{DECISION_PRINCIPLES}

{JSON_RESPONSE_FORMAT}
"""
