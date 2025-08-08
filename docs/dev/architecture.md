# Architecture v1.0.0

**Internal architecture documentation for Cogency's v1.0.0 state system.**

This document describes the implementation details of Cogency's state architecture. For user-facing documentation, see the main docs folder.

## Core Design Principles

1. **State Separation** - Clear boundaries between execution, reasoning, and memory
2. **Situated Memory** - User understanding that builds over time  
3. **Pure Functions** - Context generation without side effects
4. **Structured Facts** - No string-based cognitive fields
5. **Dictionary-based Tools** - Simple tool call representation

## State Architecture

### ExecutionState
Pure execution tracking with minimal ceremony:

```python
@dataclass
class ExecutionState:
    # Core Identity
    query: str
    user_id: str = "default"
    
    # Loop Control  
    iteration: int = 0
    max_iterations: int = 10
    mode: str = "adapt"  # "fast" | "deep" | "adapt"
    stop_reason: Optional[str] = None
    
    # Communication
    messages: List[Dict[str, str]] = field(default_factory=list)
    response: Optional[str] = None
    
    # Tool Execution (Dictionary-based)
    pending_calls: List[Dict[str, Any]] = field(default_factory=list)
    completed_calls: List[Dict[str, Any]] = field(default_factory=list)
```

### Reasoning
Structured reasoning memory without string fields:

```python
@dataclass  
class Reasoning:
    # Core Cognition (Structured Facts)
    goal: str = ""
    facts: Dict[str, Any] = field(default_factory=dict)
    strategy: str = ""
    insights: List[str] = field(default_factory=list)
    
    # Reasoning History (Simplified)
    thoughts: List[Dict[str, Any]] = field(default_factory=list)
```

### AgentState
Complete agent state combining execution + reasoning + situated memory:

```python
class AgentState:
    def __init__(self, query: str, user_id: str = "default", user_profile: Optional['UserProfile'] = None):
        self.execution = ExecutionState(query=query, user_id=user_id)
        self.reasoning = Reasoning(goal=query)  
        self.user = user_profile  # Situated memory
```

## Situated Memory Architecture

### UserProfile  
Persistent user understanding that builds over time:

```python
@dataclass
class UserProfile:
    user_id: str
    
    # Core Understanding
    preferences: Dict[str, Any] = field(default_factory=dict)
    goals: List[str] = field(default_factory=list)
    expertise_areas: List[str] = field(default_factory=list)
    communication_style: str = ""
    
    # Contextual Knowledge
    projects: Dict[str, str] = field(default_factory=dict)
    interests: List[str] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)
    
    # Interaction Patterns
    success_patterns: List[str] = field(default_factory=list)
    failure_patterns: List[str] = field(default_factory=list)
```

### ImpressionSynthesizer
LLM-driven user understanding synthesis:

```python
class ImpressionSynthesizer:
    def __init__(self, llm, store=None):
        self.llm = llm
        self.store = store
        self.synthesis_threshold = 3  # Synthesize every N interactions
        
    async def update_impression(self, user_id: str, interaction_data: Dict[str, Any]) -> UserProfile:
        # Load existing profile
        # Extract insights from interaction
        # Update profile with insights  
        # Synthesize if threshold reached
        # Save updated profile
```

## Pure Functional Context Generation

All context generation is pure functional without side effects:

```python
def reasoning_context(state: AgentState, tools: List[Any], mode: str = None) -> str:
    """Pure function: State → Reasoning Prompt."""
    # Situated memory injection
    user_context = state.get_situated_context()
    
    # Reasoning context
    reasoning_context = state.reasoning.compress_for_context()
    
    # Tool registry  
    # Recent results
    # Mode-specific instructions
    
    return formatted_prompt

def conversation_context(state: AgentState) -> List[Dict[str, str]]:
    """Pure function: State → LLM Messages."""
    return [{"role": msg["role"], "content": msg["content"]} for msg in state.execution.messages]
```

## Memory Integration

### Context Injection
User context is injected into reasoning prompts:

```python
def get_situated_context(self) -> str:
    """Get user context for prompt injection."""
    if not self.user:
        return ""
        
    from cogency.memory import compress
    context = compress(self.user)
    return f"USER CONTEXT:\n{context}\n\n" if context else ""
```

### Profile Compression
Intelligent compression for LLM context limits:

```python
def compress(profile: UserProfile, max_tokens: int = 800) -> str:
    """Generate situated context for agent initialization."""
    sections = []
    
    if profile.communication_style:
        sections.append(f"COMMUNICATION: {profile.communication_style}")
        
    if profile.goals:
        goals_str = "; ".join(profile.goals[-3:])
        sections.append(f"CURRENT GOALS: {goals_str}")
    
    # ... other profile sections
    
    result = "\n".join(sections)
    return result[:max_tokens] if len(result) > max_tokens else result
```

## Persistence Layer

### State Serialization
AgentState objects are serialized with proper datetime handling:

```python
# Filesystem store serialization
state_data = {
    "state": {
        "execution": asdict(state.execution),
        "reasoning": asdict(state.reasoning), 
        "user_profile": serialize_profile(state.user) if state.user else None,
    },
    "process_id": self.process_id,
}
```

### Profile Serialization
UserProfile datetime fields require special handling:

```python
def serialize_profile(profile: UserProfile) -> Dict[str, Any]:
    """Convert profile to dict with datetime serialization."""
    profile_dict = asdict(profile)
    profile_dict["created_at"] = profile.created_at.isoformat()
    profile_dict["last_updated"] = profile.last_updated.isoformat()
    return profile_dict

def deserialize_profile(profile_data: Dict[str, Any]) -> UserProfile:
    """Convert dict to profile with datetime deserialization."""
    data = profile_data.copy()
    if "created_at" in data:
        data["created_at"] = datetime.fromisoformat(data["created_at"])
    if "last_updated" in data:  
        data["last_updated"] = datetime.fromisoformat(data["last_updated"])
    return UserProfile(**data)
```

## Module Organization

### State Layer (`cogency.state`)
- `agent.py` - AgentState class with situated context
- `execution.py` - ExecutionState for loop control  
- `reasoning.py` - Reasoning for structured cognition
- `user_profile.py` - UserProfile data structure

### Memory Layer (`cogency.memory`)  
- `synthesizer.py` - ImpressionSynthesizer for LLM-driven updates
- `compression.py` - Profile compression utilities
- `insights.py` - Interaction insight extraction

### Persistence Layer (`cogency.persist`)
- `state.py` - StatePersistence coordinator
- `serialization.py` - Datetime serialization utilities
- `store/` - Storage implementations (filesystem, mock)

## Architectural Guarantees

**What Will NOT Change Beyond v1.0.0:**

1. ✅ Core state separation: ExecutionState vs Reasoning vs UserProfile
2. ✅ Situated memory architecture: User context injection pattern  
3. ✅ Pure functional context generation: No methods in state classes for prompt building
4. ✅ Structured facts over strings: No return to string-based cognitive fields
5. ✅ Dictionary-based tool calls: Simple implementation without custom dataclasses

**What MAY Evolve (Implementation Details Only):**

1. 🔧 Compression algorithms: Better context management strategies
2. 🔧 Tool result parsing: Enhanced extraction and validation logic
3. 🔧 Error handling: More sophisticated recovery mechanisms  
4. 🔧 Performance optimizations: Storage, serialization, async patterns
5. 🔧 Validation logic: Enhanced input sanitization and bounds checking

## Performance Considerations

- **Memory Bounds** - All collections have strict limits to prevent unbounded growth
- **Async Synthesis** - User impression updates happen in background
- **Storage Optimization** - Efficient serialization with atomic file operations
- **Context Compression** - Intelligent truncation for LLM token limits

---

*Architecture specification locked for Cogency v1.0.0*