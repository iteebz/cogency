# Architecture v1.3.0 - Cognitive Agent Features

**Key architectural features that make Cogency unique.**

This document highlights the core architectural features and design decisions that enable Cogency's cognitive capabilities. For user-facing documentation, see the main docs folder.

## Core Architectural Features

### 1. Semantic Security (Out of the Box)

Built-in semantic security assessment prevents unsafe requests:

```python
# Automatic security filtering
agent.run("rm -rf /")  # → "Security violation: Request contains unsafe content"
agent.run("Help me build a web scraper")  # → Proceeds normally
```

**Key Properties:**
- **Integrated into triage** - Security check happens before any tools are selected
- **Context-aware** - Understands intent, not just keywords
- **Zero configuration** - Works automatically without setup
- **Fail-safe** - Blocks execution entirely on security violations

### 2. Plug and Play Tooling

Tools auto-register and are intelligently selected per query:

```python
@tool
class CustomTool(Tool):
    def __init__(self):
        super().__init__("my_tool", "Does custom work")
    
    async def run(self, args: str):
        return {"result": "done"}

# Tool automatically available
agent = Agent("assistant")
agent.run("Use my_tool")  # → Automatically selects and uses CustomTool
```

**Key Properties:**
- **Auto-registration** - Tools register themselves on import
- **Intelligent selection** - Triage step chooses relevant tools per query
- **Built-in tools** - Files, Shell, Search, Scrape, Retrieve, Recall included
- **Zero configuration** - Works immediately without explicit tool lists

### 3. Adaptive Reasoning

Dynamic cognitive depth based on task complexity:

```python
# Simple query → fast mode
agent.run("What's 2+2?")  # Direct response, no tools

# Complex query → deep reasoning
agent.run("Analyze this codebase and suggest improvements")  # Multi-step reasoning with tools
```

**Reasoning Modes:**
- **Fast**: Direct responses for simple queries
- **Adapt**: Automatic mode switching based on complexity (default)
- **Deep**: Multi-iteration reasoning for complex tasks

**Key Properties:**
- **Automatic escalation** - Switches to deeper modes as needed
- **Early return** - Exits as soon as answer is ready
- **Context preservation** - Full context maintained across reasoning cycles

### 4. Built-in Resilience

Automatic error recovery and retry logic:

```python
# Tool failures don't crash execution
agent.run("List files in /nonexistent")  # → Graceful error handling

# LLM failures auto-retry
agent.run("Complex query")  # → Automatic retry on API failures
```

**Resilience Features:**
- **Tool error wrapping** - Failed tools return structured errors, don't crash
- **LLM retry logic** - Automatic retry with exponential backoff
- **Input validation** - Malformed queries handled gracefully
- **Memory failures** - Don't block user experience

### 5. Built-in Memory

Persistent context across sessions with LLM-powered synthesis:

```python
agent = Agent("assistant", memory=True)

agent.run("I prefer Python and work at Google")
agent.run("What language should I use?")  # → "Python" (remembers preference)
```

**Memory Features:**
- **User profiling** - Learns preferences, goals, communication style
- **LLM synthesis** - Intelligent consolidation of interactions
- **Trigger-based** - Updates on thresholds, session changes, high-value interactions
- **Non-blocking** - Memory operations don't slow down responses

### 6. Four-Node Architecture

Cognitive pipeline: **triage → reason → act → synthesize**

```
👤 "Build a REST API for my blog"
     ↓
🔧 TRIAGE: Selecting tools → files, shell
     ↓
🧠 REASON: Complex task → escalating to deep mode
     ↓
⚡ ACT: files(create main.py) → shell(pip install fastapi)
     ↓
🎯 SYNTHESIZE: Learning user prefers FastAPI
     ↓
🤖 "Here's your complete FastAPI blog API..."
```

**Node Responsibilities:**
- **Triage**: Tool selection, security check, early return for simple queries
- **Reason**: Adaptive thinking, mode switching, tool call generation
- **Act**: Tool execution, error handling, result integration
- **Synthesize**: Memory consolidation, user understanding updates

## Feature Integration

### Zero-Configuration Cognitive Stack

All features work together automatically:

```python
from cogency import Agent

# Single line gets you:
# ✓ Semantic security
# ✓ Adaptive reasoning  
# ✓ Tool auto-selection
# ✓ Built-in resilience
# ✓ Memory (optional)
# ✓ 4-node architecture
agent = Agent("assistant", memory=True)

result = agent.run("Help me deploy this app safely")
# → Semantic security allows safe deployment help
# → Triage selects deployment tools (files, shell)
# → Reason plans deployment steps
# → Act executes deployment commands
# → Synthesize learns about your deployment preferences
```

### Production-Ready Defaults

**Security by Default:**
- Every request automatically security-assessed
- No unsafe commands execute without explicit override
- Context-aware threat detection

**Intelligence by Default:**
- Automatic complexity detection and cognitive scaling
- Tools selected intelligently per query
- Memory synthesis without manual triggers

**Reliability by Default:**
- Error recovery built into every step
- Non-blocking memory operations
- Graceful degradation on component failures

### Observability

**Built-in Event System:**
```python
# Comprehensive execution tracing
agent.logs()  # → ["🔧 triage: selected 2 tools", "🧠 reason: iteration 1", ...]
agent.logs(mode="performance")  # → Timing analysis
agent.logs(mode="errors")  # → Error analysis
```

**Development Benefits:**
- **Clear execution flow** - See exactly what the agent is thinking
- **Performance insights** - Identify bottlenecks and optimization opportunities  
- **Error tracking** - Debug issues with detailed step-by-step traces
- **Memory insights** - Understand what the agent learns about users

## State Management (Three-Horizon Model)

The state system is organized across three temporal horizons, each with distinct persistence and lifecycle characteristics:

### Horizon 1: UserProfile (Persistent across sessions)

**Purpose**: Long-term user context that persists indefinitely

```python
@dataclass
class UserProfile:
    """Persistent user context across sessions."""
    user_id: str
    preferences: Dict[str, Any] = field(default_factory=dict)
    goals: List[str] = field(default_factory=list)
    expertise_areas: List[str] = field(default_factory=list)
    communication_style: str = ""
    projects: Dict[str, str] = field(default_factory=dict)
    interaction_count: int = 0  # LEGACY: For memory tests
    
    created_at: datetime = field(default=None)
    last_updated: datetime = field(default=None)
```

**Storage**: SQLite `user_profiles` table  
**Lifetime**: Permanent until explicitly deleted  
**Key**: `{user_id}:{process_id}`

### Horizon 2: Workspace (Task-scoped persistence)

**Purpose**: Reasoning context and insights for task continuation

```python
@dataclass
class Workspace:
    """Ephemeral task state within sessions."""
    objective: str = ""
    assessment: str = ""
    approach: str = ""
    observations: List[str] = field(default_factory=list)
    insights: List[str] = field(default_factory=list)
    facts: Dict[str, Any] = field(default_factory=dict)
    thoughts: List[Dict[str, Any]] = field(default_factory=list)
```

**Storage**: SQLite `task_workspaces` table  
**Lifetime**: Duration of task execution  
**Key**: `{task_id}` with `{user_id}` reference

### Horizon 3: ExecutionState (Runtime-only, never persisted)

**Purpose**: Current execution mechanics and conversation state

```python
@dataclass
class ExecutionState:
    """Runtime-only execution mechanics - NOT persisted."""
    iteration: int = 0
    max_iterations: int = 10
    mode: str = "adapt"
    stop_reason: Optional[str] = None
    
    messages: List[Dict[str, Any]] = field(default_factory=list)
    response: Optional[str] = None
    
    pending_calls: List[Dict[str, Any]] = field(default_factory=list)
    completed_calls: List[Dict[str, Any]] = field(default_factory=list)
    iterations_without_tools: int = 0
    tool_results: Dict[str, Any] = field(default_factory=dict)
```

**Storage**: Memory only - fresh on each agent start  
**Lifetime**: Single execution session  
**Persistence**: **NEVER** - completely runtime-only

## State Composition

The main State class composes all three horizons:

```python
@dataclass
class State:
    """Canonical Three-Horizon Split-State Model"""
    
    # Identity
    query: str
    user_id: str = "default"
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    # Three Horizons
    profile: UserProfile = field(default_factory=lambda: UserProfile(""))
    workspace: Workspace = field(default_factory=Workspace)
    execution: ExecutionState = field(default_factory=ExecutionState)
```

## SQLite Schema (Canonical)

The database schema exactly matches the Three-Horizon model:

```sql
-- Horizon 1: user_profiles table - permanent memory across sessions
CREATE TABLE user_profiles (
    user_id TEXT PRIMARY KEY,
    profile_data TEXT NOT NULL,  -- JSON serialized UserProfile
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Horizon 2: task_workspaces table - task-scoped memory for continuation
CREATE TABLE task_workspaces (
    task_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    workspace_data TEXT NOT NULL,  -- JSON serialized Workspace
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user_profiles(user_id)
);

-- Horizon 3: NO TABLE - ExecutionState is never persisted
```

## Mutation Functions

State changes happen through documented mutation functions:

```python
from cogency.state.mutations import (
    add_message,           # Adds to execution.messages
    learn_insight,         # Adds to workspace.insights
    record_observation,    # Adds to workspace.observations
    set_tool_calls,        # Sets execution.pending_calls
    finish_tools,          # Moves to execution.completed_calls
)

# Usage
add_message(state, "user", "Hello world")
learn_insight(state, "User prefers concise responses")
```

## Persistence Layer

### Store Interface (Canonical Methods)

```python
class Store(ABC):
    # Horizon 1 Operations
    async def save_user_profile(self, state_key: str, profile: UserProfile) -> bool
    async def load_user_profile(self, state_key: str) -> Optional[UserProfile]
    async def delete_user_profile(self, state_key: str) -> bool
    
    # Horizon 2 Operations  
    async def save_task_workspace(self, task_id: str, user_id: str, workspace: Workspace) -> bool
    async def load_task_workspace(self, task_id: str, user_id: str) -> Optional[Workspace]
    async def delete_task_workspace(self, task_id: str) -> bool
```

### Persistence Manager

```python
class Persistence:
    # Canonical operations
    async def user_profile(self, user_id: str, profile: UserProfile) -> bool
    async def task_workspace(self, task_id: str, user_id: str, workspace: Workspace) -> bool
    
    # Legacy compatibility (saves both horizons)
    async def save(self, state: State) -> bool
    async def load(self, user_id: str) -> Optional[State]  # Only loads UserProfile
```

## Test Environment Integration

### Autosave Detection

```python
def autosave(state: "State") -> None:
    import os
    
    # Skip autosave in test environment to prevent hanging
    if os.environ.get("PYTEST_CURRENT_TEST") or "pytest" in os.environ.get("_", ""):
        return
        
    # Normal autosave logic...
```

### MockStore Implementation

Test fixtures implement the full canonical interface:

```python
class MockStore(Store):
    def __init__(self):
        self.profiles = {}      # Horizon 1 data
        self.workspaces = {}    # Horizon 2 data
        # No storage for Horizon 3 - never persisted
```

## Migration from v1.0.x

### API Changes

```python
# OLD v1.0.x
state.reasoning.record_thinking("insight")
state.user.preferences = {"style": "concise"}
state.execution.query = "What is X?"

# NEW v1.1.x
state.workspace.thoughts.append({"thinking": "insight"})
state.profile.preferences = {"style": "concise"} 
state.query = "What is X?"  # Moved to State level
```

### Persistence Changes

```python
# OLD v1.0.x - Everything in one table
await store.save(state_key, full_state)

# NEW v1.1.x - Horizon-specific persistence
await store.save_user_profile(state_key, state.profile)      # Horizon 1
await store.save_task_workspace(task_id, user_id, state.workspace)  # Horizon 2
# Horizon 3 never persisted
```

## Performance Benefits

1. **Targeted Persistence** - Only save what needs to persist
2. **Clean Boundaries** - No accidental persistence of runtime state
3. **Test Isolation** - Proper environment detection prevents hanging
4. **Concurrent Access** - SQLite WAL mode with proper locking
5. **Schema Evolution** - Clear separation makes migrations easier

## Design Rationale

### Why Three Horizons?

1. **Conceptual Clarity** - Developers know exactly what persists
2. **Performance** - Don't persist ephemeral runtime state
3. **Testing** - Clean separation enables proper test isolation
4. **Debugging** - Clear boundaries make state issues easier to track
5. **Scalability** - Task-scoped persistence enables parallel agent execution

### Why SQLite Schema Matches State Model?

1. **No Impedance Mismatch** - Database structure mirrors code structure
2. **Type Safety** - Dataclass fields map directly to table columns
3. **Clear Ownership** - Each table owns one horizon
4. **Evolution** - Schema changes follow state model changes
5. **Debugging** - Database inspection reveals exact state structure

## Why These Features Matter

### For Production Systems

**Semantic Security** prevents agents from executing unsafe commands in production environments. No more worrying about prompt injection leading to `rm -rf /`.

**Adaptive Reasoning** means your agent scales cognitive effort appropriately - fast responses for simple queries, deep thinking for complex tasks.

**Built-in Resilience** ensures your agent doesn't crash on tool failures or API timeouts. Production reliability out of the box.

### For Developer Experience

**Plug and Play Tooling** means adding capabilities is just importing a module. No complex tool registration or configuration.

**Built-in Memory** provides persistent user context without building your own user profiling system.

**Four-Node Architecture** gives you clear observability into what your agent is thinking at each step.

### For User Experience

**Automatic complexity handling** means users get appropriate responses whether they ask "What's 2+2?" or "Analyze my codebase and suggest improvements".

**Non-blocking memory** ensures fast response times while still learning about users.

**Intelligent tool selection** means agents only use tools they need, reducing unnecessary overhead and API calls.

---

*These architectural features combine to create agents that are secure, intelligent, reliable, and easy to work with - whether you're building a simple chatbot or a complex automation system.*