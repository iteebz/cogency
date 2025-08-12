# Event System

**Zero ceremony event bus for agent observability with state-driven orchestration.**

## Usage

### Agent Logs (Retrospective)
```python
agent = Agent("assistant")
result = agent.run("Hello")
logs = agent.logs()  # Structured execution history
```

### Custom Event Handlers (Real-time)
```python
# Beautiful: just a function
def my_handler(event):
    print(f"Event: {event['type']}")

agent = Agent("assistant", handlers=[my_handler])
result = agent.run("Hello")  # Events flow to your function
```

### WebSocket Streaming Example
```python
def stream_to_websocket(event):
    ws.send(json.dumps({
        "type": event["type"],
        "data": event.get("data", {})
    }))

agent = Agent("assistant", handlers=[stream_to_websocket])
```

### Multiple Handlers Example
```python
# Queue handler
def queue_handler(event):
    queue.put(event)

# File logging  
def file_handler(event):
    with open("agent.log", "a") as f:
        f.write(f"{event}\n")

# WebSocket streaming
def websocket_handler(event):
    ws.send(json.dumps(event))

agent = Agent("assistant", handlers=[
    queue_handler,
    file_handler, 
    websocket_handler
])
```

## State-Driven Event Orchestration

**Canonical pattern: Database mutations drive events atomically.**

### Storage Operations (Automatic)
```python
# Beautiful: State mutations emit events automatically
from cogency.storage.sqlite import SQLite

store = SQLite()
result = await store.save_conversation(conversation)  
# → Automatically emits "conversation_saved" event on success
# → Atomic coupling: state change = guaranteed event
```

### Custom Storage Integration
```python
from cogency.events import state_event

@state_event("custom_saved", extract_custom_data)
async def save_custom(self, data):
    # Your state mutation logic
    success = await self._persist(data)
    return success  # Event emitted automatically based on return value

def extract_custom_data(args, kwargs, result):
    """Extract event data from method arguments."""
    data = args[1] if len(args) > 1 else kwargs.get("data")
    return {
        "entity_id": data.id,
        "user_id": data.user_id,
        "operation_type": "custom_save"
    }
```

## Event Structure

All events follow this format:
```python
{
    "type": "start|triage|reason|action|tool|respond|agent_complete|error|*_saved|*_deleted",
    "timestamp": 1234567890.12,
    "component": "agent|storage|provider",
    "success": true,  # For state-driven events
    "data": {...}     # Event-specific payload
}
```

## Event Types

### Agent Events
| Type | Purpose | Data |
|------|---------|------|
| `start` | Agent execution begins | `query` |
| `triage` | Tool selection complete | `selected_tools`, `mode` |
| `reason` | Reasoning step | `content`, `state` |
| `action` | Tool execution | `tool`, `input` |
| `tool` | Tool result | `name`, `duration`, `ok` |
| `respond` | Response generation | `content`, `state` |
| `agent_complete` | Execution finished | `source`, `iterations` |
| `error` | Failure occurred | `message`, `context` |

### State-Driven Events (Storage Operations)
| Type | Purpose | Data |
|------|---------|------|
| `conversation_saved` | Conversation persisted | `conversation_id`, `user_id`, `message_count` |
| `conversation_deleted` | Conversation removed | `target_id` |
| `profile_saved` | User profile updated | `state_key`, `user_id` |
| `profile_deleted` | User profile removed | `target_id` |
| `workspace_saved` | Task workspace persisted | `task_id`, `user_id`, `conversation_id` |
| `workspace_deleted` | Task workspace cleared | `target_id` |
| `knowledge_saved` | Knowledge artifact stored | `topic`, `user_id`, `content_type` |
| `knowledge_deleted` | Knowledge artifact removed | `target_id` |

## Implementation Notes

### Agent Events
- **Zero ceremony**: Just pass functions to `Agent(handlers=[...])`
- **Automatic wrapping**: Functions get wrapped in handler objects internally
- **Synchronous only**: Handlers process events synchronously
- **Error isolation**: Handler errors don't crash the agent  
- **Graceful degradation**: Events are optional - core logic never depends on them
- **Rolling buffer**: Built-in logger caps at 1000 events for `agent.logs()`

### State-Driven Events
- **Atomic coupling**: Events emitted only on successful state mutations
- **Canonical authority**: Database operations are single source of event truth
- **Zero race conditions**: State persistence and event emission are coupled atomically  
- **Automatic decoration**: Storage operations decorated with `@state_event()` automatically
- **Rich context**: Operation-specific metadata extracted from method arguments
- **Failure tracking**: Failed state mutations emit `success=false` events

## Architecture

```
cogency/events/
├── bus.py           # MessageBus, emit(), init_bus()
├── handlers.py      # EventBuffer, EventLogger 
├── console.py       # ConsoleHandler (terminal output)
├── orchestration.py # @state_event decorator, data extractors
├── streaming.py     # StreamingCoordinator 
└── __init__.py      # state_event export only
```

## Public API

**Agent Events**: Zero ceremony function handlers
```python
def my_handler(event): pass
agent = Agent("assistant", handlers=[my_handler])
```

**State-Driven Events**: Automatic via storage operations
```python
from cogency.events import state_event  # Only public export

@state_event("custom_saved", extract_data_func)
async def save_custom(self, data):
    return await self._persist(data)
```

**Internal Components** (don't import directly):
```python
from cogency.events.bus import MessageBus, emit  # Internal only
from cogency.events.handlers import EventBuffer   # Internal only
```

**Built-in Handlers:**
- **ConsoleHandler**: Terminal output (`[INIT]`, `[TOOL]`, `[DONE]`)
- **EventBuffer**: Structured logging for `agent.logs()` with 1000-event rolling buffer
- **EventLogger**: File-based event persistence

## Testing Strategy

Events can be disabled in tests:

```python
# Unit tests - focus on business logic
with patch("cogency.events.bus._bus", None):
    result = await execute_single_tool("search", {}, tools)
```

## Design Principles

### Beauty Doctrine Application

**"One clear way to do each thing"**: 
- Agent events → Function handlers
- State mutations → Automatic orchestrated events  
- No scattered emissions, single canonical authority

**"Delete more than create"**:
- Eliminated 37% of debug noise events (Phase 1-2)
- Zero redundant event emission patterns
- Atomic coupling removes race condition handling code

**"Canonical solutions only"**:
- Database-as-State drives all persistent observability
- Provider events follow identical schema patterns
- State-driven orchestration eliminates architectural debates

### Triple-System Telemetry Architecture

**Database-as-State** (Persistent): Conversation history, user profiles, task workspaces, knowledge artifacts
**Event Bus** (Observability): Real-time agent execution, state mutations, provider operations  
**Logging** (Operational): Debug information, error tracking, performance metrics

**Orchestration Layer**: State mutations canonically drive event emissions with atomic coupling and zero race conditions.