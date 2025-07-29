# Cognitive Scaffolding: Prompting for Structured Agent Reasoning

> Cogency is a structured reasoning system that guides LLMs through a human-like cognitive loop—analyzing complexity, adapting depth, orchestrating tools, and producing justified, structured outputs. Its architecture prioritizes clarity, robustness, and parsimony, scaffolding LLM cognition through well-defined phases and contract-like prompts. Multiple models independently affirm its alignment with both best practices and model incentives. This isn’t another “tool-using wrapper”—it’s a framework for intelligent action.

## Overview

Cogency's prompts implement **cognitive scaffolding** - structured frameworks that guide LLMs through explicit reasoning processes rather than generic "be helpful" instructions. This approach creates consistent, auditable, and adaptive agent behavior.

## Core Principles

### 1. JSON-First Design
- **Schema upfront**: Always show expected JSON structure before instructions
- **No markdown fences**: Avoid `\`\`\`json` blocks that models may echo back
- **Concrete examples**: Include realistic JSON examples showing complete responses

### 2. Explicit Reasoning Frameworks
Each prompt provides clear cognitive scaffolding:
- **Memory → Complexity → Tools** (preprocessing)
- **Assess → Reflect → Plan → Execute** (deep reasoning) 
- **Think → Act** (fast reasoning)
- **Synthesize → Format** (response generation)

### 3. Scenario-Specific Strategies
Rather than generic instructions, each prompt includes targeted **RESPONSE STRATEGY** sections:
- Tool failure: "Acknowledge gracefully, suggest alternatives"
- JSON response: "Populate fields exactly, synthesize don't dump"
- Tool synthesis: "Lead with direct answer, use results as evidence"
- Knowledge-only: "Answer directly, acknowledge limitations"

## Architecture Integration

### Cognitive Parsimony
The fast/deep switching embodies **"thinking as hard as needed, no more"** - mirroring human cognition where simple tasks don't require deep analysis.

### Externalized Cognition  
Every decision includes explicit reasoning that is:
- **Auditable**: Clear chain of thought in `reasoning` fields
- **Debuggable**: Visible decision processes for troubleshooting
- **Traceable**: Complete execution paths through agent state

### Memory as First-Class Citizen
Structured separation of:
- **Extractive facts**: `"memory": "User building React app"`
- **Interpretive tags**: `"tags": ["coding", "frontend"]"`
- **Persistence strategy**: Explicit memory_type classification

## Template Design Patterns

### Clean Separation of Concerns
```python
# BAD: Monolithic prompt function with embedded strings
def prompt_response(...):
    if scenario_a:
        return f"""Massive embedded string with {variables}..."""

# GOOD: Template extraction with routing logic  
SCENARIO_A_PROMPT = """Clean template with {variables}"""

def prompt_response(...):
    return SCENARIO_A_PROMPT.format(variables=values)
```

### Concrete Decision Criteria
```python
# BAD: Vague classification
"Choose fast or deep mode based on complexity"

# GOOD: Concrete signals
"""
🎯 COMPLEXITY: Classify using concrete signals:
   - FAST: Single factual lookup, basic calculation, direct command
   - DEEP: Multiple sources needed, comparison/synthesis, creative generation
"""
```

## Multi-Model Co-Design Methodology

**Unique Approach**: We directly asked different LLMs "How would you like to be prompted?" in first-person, then synthesized their preferences into unified implementations.

### First-Person Prompt Feedback
Each model was asked to analyze existing prompts and provide first-person feedback:
- **"How would you like to be prompted for preprocessing?"**
- **"What response generation format works best for you?"** 
- **"What reasoning structure helps you think clearly?"**

### Model-Specific Insights
- **Claude**: Preferred structured reasoning phases, explicit role definition, JSON-first format
- **ChatGPT**: Emphasized fallback robustness, deterministic routing, concrete behavioral guidance
- **Gemini**: Wanted JSON schema upfront, concrete classification criteria, clear cognitive frameworks

### Consensus Patterns
All models consistently preferred:
1. **Role clarity upfront**: "You are a preprocessing agent responsible for..."
2. **Structured information flow**: Role → Format → Context → Strategy  
3. **Concrete behavioral guidance**: Specific actions over vague directives
4. **JSON-first design**: Schema before instructions, no markdown fences
5. **Explicit reasoning requirements**: Forced justification in response structure

## Production Benefits

### Self-Healing Flows
Robust fallback paths prevent dead ends:
- Tool failures → graceful error synthesis
- JSON parsing errors → structured recovery
- Reasoning loops → adaptive mode switching

### Scalable Cognition
- **Adaptive effort**: Fast mode for simple tasks, deep mode for complex ones
- **Tool selection**: Dynamic filtering vs shotgun approach
- **Memory integration**: Context-aware reasoning without overwhelming prompts

### Maintainable Templates
- **Scannable**: Each template fits on screen, easy to understand
- **Modular**: Independent templates for different scenarios  
- **Extensible**: Clear patterns for adding new response types

## Key Insights

1. **Structured cognition beats generic prompting**: Explicit frameworks outperform "be helpful" instructions
2. **Template extraction improves readability**: Separate templates from routing logic for maintainability  
3. **Concrete criteria reduce hallucination**: Specific decision signals prevent model drift
4. **Forced reasoning enables debugging**: Explicit justification makes agent decisions auditable
5. **Cognitive scaffolding scales**: Same patterns work across different models and scenarios

## Future Directions

- **Prompt variants**: Model-specific optimizations while maintaining core scaffolding
- **Evaluation metrics**: Quality scoring for reasoning coherence and decision accuracy
- **Dynamic scaffolding**: Adaptive prompt complexity based on task difficulty
- **Reflection loops**: Self-correction mechanisms using reasoning traces