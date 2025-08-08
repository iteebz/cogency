# Cogency State Architecture v2.1 - CANONICAL

**LOCKED SPECIFICATION - Implementation must match exactly**

## Three-Horizon Split-State Model

### Horizon 1: Permanent Memory (UserProfile)
- **Lifecycle**: Permanent - survives across all tasks and sessions
- **Purpose**: Long-term user identity, preferences, goals, expertise
- **Persistence**: `user_profiles` table, indexed by `user_id`
- **Scope**: User-scoped

### Horizon 2: Task-Scoped Workspace  
- **Lifecycle**: Task-scoped - created on task start, deleted on task completion
- **Purpose**: Intermediate context, plans, discoveries for ONE specific task
- **Persistence**: `task_workspaces` table, indexed by `task_id` + `user_id`
- **Scope**: Task-scoped (allows task continuation without cross-task pollution)

### Horizon 3: Runtime Execution
- **Lifecycle**: Runtime-only - exists only during active execution
- **Purpose**: Low-level mechanics (messages, iterations, tool calls)
- **Persistence**: NONE - never saved to database
- **Scope**: Execution-scoped

## Data Structures

```python
@dataclass
class UserProfile:
    """Permanent user context - Horizon 1"""
    user_id: str
    preferences: Dict[str, Any] = field(default_factory=dict)
    goals: List[str] = field(default_factory=list)
    expertise_areas: List[str] = field(default_factory=list)
    communication_style: str = ""
    projects: Dict[str, str] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)

@dataclass
class Workspace:
    """Task-scoped working memory - Horizon 2"""
    objective: str = ""
    assessment: str = ""
    approach: str = ""
    observations: List[str] = field(default_factory=list)
    insights: List[str] = field(default_factory=list)
    facts: Dict[str, Any] = field(default_factory=dict)
    thoughts: List[Dict[str, Any]] = field(default_factory=list)

@dataclass
class ExecutionState:
    """Runtime-only mechanics - Horizon 3"""
    iteration: int = 0
    max_iterations: int = 10
    mode: str = "adapt"
    stop_reason: Optional[str] = None
    messages: List[Dict[str, Any]] = field(default_factory=list)
    response: Optional[str] = None
    pending_calls: List[Dict[str, Any]] = field(default_factory=list)
    completed_calls: List[Dict[str, Any]] = field(default_factory=list)
    iterations_without_tools: int = 0

@dataclass
class State:
    """Complete agent state with three horizons"""
    # Identity
    query: str
    user_id: str = "default"
    task_id: str = field(default_factory=lambda: str(uuid4()))
    
    # Three horizons
    profile: UserProfile = None       # Horizon 1 - Permanent
    workspace: Workspace = None       # Horizon 2 - Task-scoped
    execution: ExecutionState = None  # Horizon 3 - Runtime-only
```

## Explicit Task Lifecycle Management

### 1. Task Initiation
```python
# Create new task with fresh workspace
state = await State.start_task(
    query="analyze codebase", 
    user_id="alice"
)
# Loads existing UserProfile from user_profiles table
# Creates fresh Workspace and saves to task_workspaces table
# Creates fresh ExecutionState (runtime-only)
```

### 2. Task Continuation  
```python
# Resume existing task with preserved workspace
state = await State.continue_task(
    task_id="task-uuid-123",
    user_id="alice"
)
# Loads UserProfile from user_profiles table
# Loads existing Workspace from task_workspaces table
# Creates fresh ExecutionState (runtime-only)
```

### 3. Task Completion
```python
# Finalize task and cleanup workspace
await state.complete_task()
# Saves any UserProfile updates to user_profiles table
# DELETES workspace from task_workspaces table
# ExecutionState discarded (never persisted)
```

## Database Schema

### Table: user_profiles
```sql
CREATE TABLE user_profiles (
    user_id TEXT PRIMARY KEY,
    profile_data TEXT NOT NULL,  -- JSON serialized UserProfile
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Table: task_workspaces  
```sql
CREATE TABLE task_workspaces (
    task_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    workspace_data TEXT NOT NULL,  -- JSON serialized Workspace
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user_profiles(user_id)
);
```

### NO Table for ExecutionState
- ExecutionState is NEVER persisted to database
- Rebuilt fresh on each execution

## Persistence Strategy

### What Gets Persisted:
- **UserProfile**: Always → `user_profiles` table
- **Workspace**: During task lifecycle → `task_workspaces` table
- **ExecutionState**: NEVER

### Persistence Operations:
```python
# During task execution - autosave both horizons
def autosave(state: State):
    # Save UserProfile updates
    save_user_profile(state.user_id, state.profile)
    
    # Save Workspace updates for task continuation
    save_task_workspace(state.task_id, state.user_id, state.workspace)
    
    # ExecutionState NEVER saved

# On task completion - cleanup workspace
def complete_task(state: State):
    # Save final UserProfile updates
    save_user_profile(state.user_id, state.profile)
    
    # DELETE workspace - task finished
    delete_task_workspace(state.task_id)
```

## Execution Flow

### Session Start:
1. Load UserProfile from `user_profiles` table (or create if new user)
2. Create fresh Workspace for new task OR load existing for task continuation  
3. Create fresh ExecutionState (always runtime-only)
4. Assemble State with all three horizons

### During Execution:
1. Agent operates on complete State
2. Autosave triggers save UserProfile + Workspace (NOT ExecutionState)
3. ExecutionState updated in-memory only

### Session End:
1. Save UserProfile updates to `user_profiles` table
2. Save Workspace updates to `task_workspaces` table (if task continues)
3. Discard ExecutionState completely (never persisted)
4. On task completion: DELETE workspace from `task_workspaces`

## ACID Compliance

- **Atomicity**: Each save operation is atomic (UserProfile and Workspace saved together)
- **Consistency**: Foreign key constraints ensure data integrity
- **Isolation**: Concurrent tasks isolated by task_id
- **Durability**: SQLite/database ensures persistence survives crashes

## Benefits Achieved

✅ **Task Continuation**: Workspace persists for resumable tasks
✅ **Clean Boundaries**: Three distinct horizons with clear semantics  
✅ **No Cross-Task Pollution**: Each task gets isolated workspace
✅ **Explicit Lifecycle**: start_task/continue_task/complete_task control
✅ **Database-as-State**: ACID persistence with targeted scope
✅ **Performance**: Only relevant data persisted, no runtime bloat

## Implementation Requirements

1. **State must have task_id field**
2. **Storage backends must support both user_profiles AND task_workspaces tables**
3. **Lifecycle methods (start_task, continue_task, complete_task) must be implemented**
4. **Autosave must persist UserProfile + Workspace (NOT ExecutionState)**
5. **Task completion must DELETE workspace to prevent accumulation**

---

**THIS IS THE CANONICAL ARCHITECTURE - IMPLEMENTATION MUST MATCH EXACTLY**