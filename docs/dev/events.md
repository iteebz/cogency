# Event System

**Tactical message bus for agent observability - minimal and fast.**

## Architecture

```
cogency/events/
├── core.py      # MessageBus, emit(), decorators
├── handlers.py  # ConsoleHandler, LoggerHandler, MetricsHandler, CallbackHandler
└── __init__.py  # Clean imports
```

## Usage

### Zero Ceremony
```python
from cogency.events import emit

emit("start", query="Hello")
emit("tool", name="search", duration=1.2, ok=True)
```

### Canonical Agent API
```python
# Zero ceremony
agent = Agent("assistant")
result = await agent.run_async("Hello")
logs = agent.logs()  # Structured events

# Custom event streaming
def stream_to_websocket(event):
    ws.send(json.dumps(event))

agent = Agent("assistant", handlers=[CallbackHandler(stream_to_websocket)])
result = await agent.run_async("Hello")  # Events stream to WebSocket
```

## Components

### MessageBus
Core event router. Handlers subscribe, events flow.

### Handlers
- **ConsoleHandler**: Real-time terminal feedback with emojis
- **LoggerHandler**: Rolling buffer for `agent.logs()`
- **MetricsHandler**: Performance data collection
- **CallbackHandler**: Custom event callbacks (WebSockets, streaming, etc)

### Decorators
- `@component(name)`: Setup/teardown events
- `@lifecycle(event)`: Creation/destruction events  
- `@secure`: Security operation events

## Event Types

| Type | Purpose | Data |
|------|---------|------|
| `start` | Agent execution begins | `query` |
| `triage` | Tool selection complete | `selected_tools` |
| `tool` | Tool execution | `name`, `duration`, `ok` |
| `respond` | Response generation | `state` |
| `error` | Failure occurred | `message` |

## Streaming Patterns

```python
# WebSocket streaming
def websocket_handler(event):
    ws.send(json.dumps(event))

# Queue streaming  
def queue_handler(event):
    queue.put(event)

# File logging
def file_handler(event):
    log_file.write(f"{event}\n")

agent = Agent("assistant", handlers=[
    CallbackHandler(websocket_handler),
    CallbackHandler(queue_handler),
    CallbackHandler(file_handler)
])
```

## Implementation Notes

- **Global bus**: `init_bus(bus)` once, `emit()` anywhere
- **No async**: Handlers process synchronously  
- **Structured logs**: Flattened format for easy access
- **Noise filtering**: Config events filtered by default
- **Rolling buffer**: LoggerHandler caps at 1000 events
- **Custom handlers**: Add via `Agent(handlers=[...])`
- **Graceful degradation**: Events are optional - core logic never depends on them

## Private API (v1.0.0)

Only `CallbackHandler` is publicly exported. All other components are internal:

```python
# Public API
from cogency.events import CallbackHandler

# Internal (not exported)
from cogency.events.core import MessageBus, emit, init_bus
from cogency.events.handlers import ConsoleHandler, LoggerHandler
```

## Testing Strategy

Events can be cleanly disabled in tests without breaking functionality:

```python
# Unit tests - disable events to focus on business logic
with patch("cogency.events.core._bus", None):
    result = await execute_single_tool("search", {}, tools)
```

## Legacy Removal

**Eliminated**: Old `notify` system, `Notification` class, dual emit patterns, bloated `stream()` method.

**Result**: Single unified event system, zero ceremony, beautiful API, v1.0.0 ready.