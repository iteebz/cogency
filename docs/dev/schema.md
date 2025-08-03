# Cogency Schema: LLM-Native State Architecture

> **Core Principle**: Names must facilitate LLM slot-filling behavior and eliminate semantic ambiguity across reasoning boundaries.

## Schema Overview

Cogency uses three distinct semantic layers to separate concerns cleanly:

- **Memory**: Persistent user context across sessions
- **Workspace**: Ephemeral reasoning state within tasks  
- **Reasoning**: Active thought process and decision output

## Memory Schema (Persistent)

```python
class Memory:
    impression: str     # Synthesized long-term user model
    recent: str        # Temporary interaction buffer (cleared after synthesis)
    
    def recall() -> str:  # Retrieve memory context for reasoning
```

**Semantic Boundaries:**
- `impression` - Compressed understanding of user identity, preferences, patterns
- `recent` - Raw interaction buffer since last synthesis (ephemeral, rotating)
- `recall()` - Developer-intent function for memory retrieval

**Key Insight:** `impression` avoids semantic collision with workspace `assessment` - different types of understanding for different scopes.

## Workspace Schema (Ephemeral)

```python
class State:
    # Task execution context
    objective: str      # Current goal the agent is pursuing
    assessment: str     # Analysis of current problem, facts, constraints  
    approach: str       # Strategy/method for achieving objective
    observations: str   # Accumulated evidence from tool execution
```

**Semantic Boundaries:**
- `objective` - Clear goal state, activates purpose-driven reasoning
- `assessment` - Problem analysis, distinct from user `impression`
- `approach` - Method/strategy, suggests planning behavior
- `observations` - Empirical evidence, progressive accumulation

## Reasoning Output Schema

```python
@dataclass
class Reasoning:
    thinking: str           # Internal monologue/chain-of-thought
    tool_calls: List[ToolCall]  # Actions to execute
    updates: dict          # Proposed workspace modifications
```

**Semantic Boundaries:**
- `thinking` - Internal reasoning process, matches chain-of-thought patterns
- `tool_calls` - Concrete actions, clear execution intent
- `updates` - Simple change dictionary, avoids computational abstractions

## Design Principles

### 1. Semantic Precision
- **No overloaded terms**: `assessment` vs `impression` eliminates understanding collision
- **Scope-specific naming**: Memory terms suggest persistence, Workspace suggests ephemeral state
- **Action clarity**: `recall()` expresses developer intent, not implementation detail

### 2. LLM-Native Alignment  
- **Slot-filling optimization**: Names suggest expected content structure
- **Prior alignment**: Terms match documentation/dialogue patterns in training data
- **Cognitive mapping**: Schema mirrors human reasoning: memory → assessment → planning → action

### 3. Architectural Integrity
- **Implementation accuracy**: `recent` buffer gets cleared, not persistent `history`
- **Clean separation**: Memory/Workspace boundaries prevent state leakage
- **Minimal abstraction**: Simple terms over technical jargon (`updates` vs `StateDelta`)

## Usage Examples

### Memory Integration
```python
# Learning from interaction
await memory.remember("User prefers TypeScript", human=True)

# Context injection  
memory_context = await memory.recall()
prompt = f"{memory_context}\n\nUser query: {query}"
```

### Workspace Updates
```python
# Reasoning output updates workspace
reasoning = Reasoning(
    thinking="User wants to build a React app...",
    tool_calls=[ToolCall("create_file", {"path": "app.tsx"})],
    updates={
        "objective": "Create React TypeScript application",
        "assessment": "User needs modern React setup with TypeScript",
        "approach": "Use Vite for fast development setup"
    }
)
```

### Context Building
```python
# Clean context assembly
memory_context = await memory.recall()
workspace_context = state.get_workspace_context()

reasoning_prompt = f"""
{memory_context}

CURRENT TASK:
{workspace_context}

What should I do next?
"""
```

## Implementation Status

### Step 1: Complete ✅
- Memory class with `impression`/`recent` fields
- Workspace with `objective`/`assessment`/`approach`/`observations`  
- Reasoning output with `thinking`/`tool_calls`/`updates`
- Clean API boundaries and semantic separation

### Step 2: Validation
- Cross-session persistence for Memory schema
- Workspace context optimization for different reasoning modes
- Schema validation and type safety improvements

## Success Criteria

- [x] Zero semantic collision between schema layers
- [x] LLM slot-filling optimization through intuitive naming
- [x] Implementation accuracy (schema matches actual behavior)
- [x] Clean separation of persistent vs ephemeral context
- [x] Minimal abstraction overhead

**Result**: Schema enables natural LLM reasoning without cognitive load from ambiguous or conflicting terminology.