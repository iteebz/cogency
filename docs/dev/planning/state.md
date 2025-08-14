# Cogency State Architecture v5.0 - CANONICAL SPECIFICATION

**Three-Component State Model + Memory Domain Profile Injection + 4-Field Workspace**

## Architecture Overview

Cogency uses a three-component state model with profile injection from the memory domain. This architecture enables conversation persistence, cognitive workspace reasoning, and clean domain separation.

## Domain Architecture

### State Domain (3 Components)
Task-scoped and conversation-scoped state management.

### Memory Domain (Profile Injection)
User profile lives in `memory/` domain and gets injected during context assembly via `memory.activate(user_id)`.

## Three State Components

### 1. Conversation (Persistent History)
- **Lifecycle**: Conversation-scoped - survives across multiple tasks within same conversation
- **Purpose**: Message history for conversation continuity
- **Persistence**: `conversations` table, indexed by `conversation_id` + `user_id`
- **Scope**: Conversation-scoped threading

### 2. Workspace (Task-Scoped Cognitive Context)
- **Lifecycle**: Task-scoped - created on task start, deleted on task completion
- **Purpose**: Cognitive workspace with semantic fields for superior LLM reasoning
- **Persistence**: `task_workspaces` table, indexed by `task_id` + `user_id`
- **Scope**: Task-scoped cognitive working memory

### 3. Execution (Runtime-Only)
- **Lifecycle**: Runtime-only - exists only during active execution
- **Purpose**: Low-level execution mechanics (iterations, tool calls, current response)
- **Persistence**: NONE - never saved to database
- **Scope**: Execution-scoped runtime state

## Data Structures

```python
@dataclass
class Conversation:
    """Persistent conversation history across tasks."""
    conversation_id: str = field(default_factory=lambda: str(uuid4()))
    user_id: str = ""
    messages: List[Dict[str, Any]] = field(default_factory=list)
    last_updated: datetime = field(default_factory=datetime.now)

@dataclass
class Workspace:
    """Task-scoped cognitive workspace for natural LLM reasoning.
    
    4-Field Minimalist Architecture: Provides clear semantic boundaries without
    fragmenting cognition. Enables natural reasoning flows while maintaining
    parseable structure for context assembly.
    """
    objective: str = ""      # "What we're trying to achieve"
    understanding: str = ""  # "What we've learned and know"  
    approach: str = ""       # "How we're tackling this systematically"
    discoveries: str = ""    # "Key insights, patterns, breakthroughs"

@dataclass
class Execution:
    """Runtime-only execution mechanics."""
    iteration: int = 0
    max_iterations: int = 10
    stop_reason: str | None = None
    messages: List[Dict[str, Any]] = field(default_factory=list)
    response: str | None = None
    pending_calls: List[Dict[str, Any]] = field(default_factory=list)
    completed_calls: List[Dict[str, Any]] = field(default_factory=list)
    iterations_without_tools: int = 0
    tool_results: Dict[str, Any] = field(default_factory=dict)

@dataclass
class State:
    """Complete agent state with three components + memory domain profile injection."""
    # Identity
    query: str
    user_id: str = "default"
    task_id: str = field(default_factory=lambda: str(uuid4()))
    
    # Three state components
    conversation: Conversation = None # Persistent message history
    workspace: Workspace = None       # Task-scoped cognitive context
    execution: Execution | None = None # Runtime-only mechanics
    
    # Security
    security_assessment: str | None = None
    
    # State metadata
    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)
```

## Profile Domain Injection

**Profile is NOT in State** - it lives in the `memory/` domain and gets injected during context assembly:

```python
# Profile lives in memory/ domain
class Agent:
    async def build_context(self, state, tools, memory, iteration):
        """Cross-domain context assembly - NOT state.context()"""
        parts = []
        
        # Memory domain - Profile injection FIRST
        if memory:
            profile_context = await memory.activate(state.user_id)  
            if profile_context:
                parts.append(profile_context)
        
        # State domain components
        workspace_context = self._build_workspace_context(state.workspace)
        execution_context = self._build_execution_context(state.execution)
        parts.extend([workspace_context, execution_context])
        
        # Tools domain LAST
        tool_registry = self._build_tool_registry(tools)
        parts.append(tool_registry)
        
        return "\n\n".join(parts)
```

## Canonical Context Assembly Pattern

**Historical Discovery**: Through git archaeology, we found the canonical ordering and style:

```python
# Canonical order (from 2025-08-04 design logs)
parts = []
if memory: parts.append(memory_context)      # Memory domain FIRST
parts.append(workspace_context)              # Workspace state
parts.append(execution_context)              # Runtime state  
parts.append(tools_context)                  # Tools domain LAST
return "\n\n".join(parts)                    # Double newline separation, no adornments
```

**Context Assembly Principles**:
- **Memory first** - Stable user frame for LLM interpretation
- **Tools last** - Actionable options, not situational facts
- **Double newline separation** - Clean visual boundaries
- **Agent assembles, not State** - Context cuts across domains

## Workspace Field Design: 4-Field vs 7-Field Decision

**Architectural Decision Process**: Extensive council evaluation between minimalist 4-field and structured 7-field workspace models.

### Historical Context

**Original Canonical (4 fields)**:
```python
objective: str = ""      # "What we're trying to achieve"
understanding: str = ""  # "What we've learned and know"  
approach: str = ""       # "How we're tackling this systematically"
discoveries: str = ""    # "Key insights, patterns, breakthroughs"
```

**Alternative 7-Field Model** - Considered but rejected:
- Split `understanding` → `assessment` (current progress evaluation)
- Split `discoveries` → `observations` + `insights` + `facts` + `thoughts`

### Council Evaluation

**Arguments for 7-Field**:
- Structured cognitive scaffolding forces LLM to separate raw data from conclusions
- Auditability through explicit categorization of observations vs insights
- Machine-readable facts dictionary for structured data storage
- Meta-reasoning trail through thoughts history

**Arguments for 4-Field** (Winning Position):
- Natural LLM reasoning flows without artificial taxonomic constraints
- Reduced cognitive overhead from meta-categorization decisions
- Fault-tolerant design - semantic drift recoverable, parsing failures are not
- Evolutionary architecture - can add structure when empirically proven necessary

### Decision Factors

**Key Factor: Immutability Constraint Removed**
- With iterative evolution possible, minimalism wins over premature optimization
- Start simple, measure actual reasoning quality, evolve based on evidence
- Avoid solving theoretical problems instead of real ones

**Evidence from Implementation**:
```python
# Current implementation shows manual curation needed for 7-field:
if self.workspace.observations:
    parts.append(f"OBSERVATIONS: {'; '.join(self.workspace.observations[-3:])}")
```
This curation requirement proves the structure creates noise that needs filtering.

**LLM Council Split Decision**:
- **Claude instances**: Favored 4-field for cognitive elegance and CLAUDE.md alignment
- **Gemini + ChatGPT**: Initially favored 7-field for production rigor
- **ChatGPT final position**: Flipped to 4-field when immutability constraint removed

### Final Reasoning

**4-Field Cognitive Advantages**:
1. **Natural Reasoning**: LLMs synthesize information naturally within semantic boundaries
2. **Reduced Friction**: No meta-cognitive overhead deciding "is this insight or observation?"
3. **Fault Tolerance**: Natural language more resilient than rigid JSON schemas
4. **Context Efficiency**: No accumulation bloat requiring manual curation

**Design Philosophy**: 
- **Trust LLM cognition** rather than impose artificial taxonomies
- **Optimize for reasoning quality** over human code review aesthetics  
- **Evolutionary simplicity** - add complexity when proven necessary, not theoretically justified

## Pure ReAct Implementation

**Canonical Simplification**: Moved from complex mode switching to pure ReAct where LLM decides reasoning depth naturally:

```python
async def reason(state, llm, tools, identity="") -> dict:
    """Pure ReAct - single LLM call, natural depth autonomy"""
    
    # Cross-domain context assembly
    context = agent.build_context(state, tools, memory, state.execution.iteration)
    
    # Security only on first iteration
    security = SECURITY_PROMPT if state.execution.iteration == 1 else ""
    
    # Single prompt with 4-field workspace
    prompt = f"""
    {identity}
    {security}
    
    CONTEXT:
    {context}
    
    Respond with JSON containing workspace fields:
    {{
      "secure": true,                           // first iteration only
      "objective": "refined goal",              
      "understanding": "what we've learned and know",
      "approach": "how we're tackling this systematically", 
      "discoveries": "key insights, patterns, breakthroughs",
      "response": "direct answer or null",
      "actions": [{{"name": "tool_name", "args": {{"param": "value"}}}}]
    }}
    """
    
    # Single LLM call - no orchestration, let LLM decide depth
    messages = build_conversation_messages(state, prompt)
    result = await llm.generate(messages)
    
    # Parse and update workspace semantically
    parsed = parse_and_validate(result)
    update_workspace_from_reasoning(state.workspace, parsed)
    
    return parsed
```

## Architecture Benefits

✅ **Natural LLM Reasoning**: Semantic boundaries without cognitive fragmentation  
✅ **Clean Domain Separation**: Profile in memory/, State focused on task/conversation  
✅ **Cross-Domain Context**: Context assembly cuts across domains as it should  
✅ **Conversation Continuity**: Messages persist across multiple tasks  
✅ **Pure ReAct Simplicity**: No mode switching, natural LLM depth autonomy  
✅ **Canonical Implementation**: Single reason function, single context builder  
✅ **Evolutionary Architecture**: Start minimal, evolve based on empirical evidence
✅ **Production Ready**: Clean persistence boundaries, ACID compliance  

## Implementation Contract

**The JSON schema is the contract** - workspace mirrors all 4 fields exactly:
- **No selective omission** - All fields available to LLM every iteration
- **Schema validation** - Failed validation triggers retry with schema reminder  
- **Natural updates** - Each field updates workspace state with LLM-structured content
- **Depth autonomy** - LLM determines reasoning depth and organization naturally

## Critical Design Principles

**From Historical Analysis (2025-07-21 to 2025-08-04)**:

1. **Agent-State Separation**: "State holds facts; Agent holds intelligence to assemble them"
2. **Memory Injection Ordering**: "Always inject memory context first... Tools go last"  
3. **Iteration Sensitivity**: "Security preamble only on iteration 1"
4. **Reasoning Contract**: "JSON schema is the contract... workspace mirrors schema exactly"
5. **Depth Autonomy**: "LLM determines how far to reason in a single call"
6. **Canonical Simplicity**: "One build_context. One reason. One workspace update."
7. **Evolutionary Minimalism**: "Start simple, measure quality, evolve based on evidence"

---

**ARCHITECTURE STATUS: CANONICAL AND FINAL**
- Three-component state model with memory domain profile injection
- Four-field workspace optimized for natural LLM reasoning flows
- Pure ReAct implementation with natural depth autonomy
- Cross-domain context assembly pattern established
- Evolutionary architecture enabling empirical refinement
- Production-ready conversation persistence and multitenant support