# Memory Architecture - Universal Context Injection

**Canonical Memory System Design for Extensible Agent Architecture**

## Architectural Principle

**Memory** = Persistent cross-session context injection  
**State** = Ephemeral execution context

Clean separation of concerns enables universal memory extensibility.

## Core Abstraction

### Memory Interface

```python
from abc import ABC, abstractmethod

class Memory(ABC):
    """Universal persistent context injection interface."""
    
    @abstractmethod
    def load(self, context_id: str) -> None:
        """Load persistent context from storage."""
        
    @abstractmethod
    def context(self) -> str:
        """Generate context string for agent injection."""
        
    @abstractmethod
    def remember(self, content: str, metadata: dict = None) -> None:
        """Update persistent context with new information."""
```

### Profile - First Memory Primitive

```python
@dataclass
class Profile(Memory):
    """User identity and preferences memory primitive.
    
    Direct context injection of user profile data for consistent
    agent behavior across sessions.
    """
    
    user_id: str
    preferences: dict = field(default_factory=dict)
    communication_style: str = ""
    expertise_areas: list = field(default_factory=list)
    
    def context(self) -> str:
        """Generate user context for agent injection."""
        parts = []
        
        if self.communication_style:
            parts.append(f"Communication style: {self.communication_style}")
            
        if self.expertise_areas:
            parts.append(f"User expertise: {', '.join(self.expertise_areas)}")
            
        if self.preferences:
            prefs = [f"{k}: {v}" for k, v in self.preferences.items()]
            parts.append(f"Preferences: {'; '.join(prefs)}")
            
        return "\n".join(parts) if parts else ""
```

## Architectural Transformation

### Before: Mixed Concerns

```python
# State mixed persistent and ephemeral concerns
@dataclass
class State:
    execution: Execution      # Ephemeral
    conversation: Conversation  # Ephemeral
    workspace: Workspace      # Ephemeral
    profile: Profile          # PERSISTENT (architectural inconsistency)
```

### After: Clean Separation

```python
# Pure ephemeral execution context
@dataclass  
class State:
    execution: Execution      # Current reasoning state
    conversation: Conversation # Current dialog
    workspace: Workspace      # Task scratchpad
    # profile moved to Memory domain

# Universal persistent context injection
class Memory(ABC):
    # Abstract interface for any persistent context
    
class Profile(Memory):
    # User identity memory primitive
```

## Agent Integration

### Clean Memory-State Usage

```python
# Before: Unclear mixed interface
Agent(memory=True)  # What does this enable?

# After: Explicit memory sources
Agent(
    memory=Profile(user_id="user123"),  # Persistent context
    # State remains pure ephemeral execution context
)
```

## Extensibility Patterns

The universal Memory interface enables natural extensions:

### Project Memory
```python
class ProjectMemory(Memory):
    """Codebase understanding and patterns memory."""
    
    def __init__(self, codebase_id: str):
        self.codebase_id = codebase_id
        self.patterns = {}
        self.architecture_insights = []
        
    def context(self) -> str:
        return f"Codebase patterns: {self.patterns}\nArchitecture: {self.architecture_insights}"
```

### Domain Memory
```python
class DomainMemory(Memory):
    """Specialized expertise and knowledge memory."""
    
    def __init__(self, domain: str):
        self.domain = domain
        self.expertise = {}
        self.best_practices = []
        
    def context(self) -> str:
        return f"Domain expertise in {self.domain}: {self.expertise}"
```

### Collaborative Memory
```python
class CollaborativeMemory(Memory):
    """Multi-agent shared context memory."""
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.shared_context = {}
        
    def context(self) -> str:
        return f"Shared context: {self.shared_context}"
```

### Composable Memory Sources

```python
# Future extensible agent with multiple memory sources
Agent(
    memory=[
        Profile(user_id="user123"),
        ProjectMemory(codebase_id="cogency"),
        DomainMemory(domain="python"),
        CollaborativeMemory(session_id="team_review")
    ]
)
```

## Implementation Strategy

### Phase 1: Foundation
1. Extract Profile from State architecture
2. Implement Memory interface
3. Update Agent class for Memory-State separation

### Phase 2: Extensibility  
1. Document extension patterns
2. Implement ProjectMemory as second primitive
3. Add multi-memory composition support

### Phase 3: Advanced Features
1. Memory source prioritization
2. Context conflict resolution
3. Dynamic memory loading/unloading

## Architectural Benefits

**Clean Separation**: Memory and State have distinct responsibilities
**Extensibility**: Universal interface supports any persistent context type
**Composability**: Multiple memory sources can be combined naturally
**Maintainability**: Each memory type is self-contained with clear interface

## Success Metrics

- Profile successfully extracted from State
- Zero functional regression in agent behavior
- Memory interface documented and implemented
- Agent class updated for clean separation
- Extension patterns documented for future development

---

This architecture establishes Memory as a universal cognitive primitive rather than user-specific feature, enabling natural extension to any persistent context injection need.