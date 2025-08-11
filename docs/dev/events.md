# Event System

**Zero ceremony event bus for agent observability.**

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

## Event Structure

All events follow this format:
```python
{
    "type": "start|triage|reason|action|tool|respond|agent_complete|error",
    "timestamp": 1234567890.12,
    "data": {...}  # Event-specific payload
}
```

## Event Types

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

## Implementation Notes

- **Zero ceremony**: Just pass functions to `Agent(handlers=[...])`
- **Automatic wrapping**: Functions get wrapped in handler objects internally
- **Synchronous only**: Handlers process events synchronously
- **Error isolation**: Handler errors don't crash the agent  
- **Graceful degradation**: Events are optional - core logic never depends on them
- **Rolling buffer**: Built-in logger caps at 1000 events for `agent.logs()`

## Architecture

```
cogency/events/
├── core.py      # MessageBus, emit(), decorators
├── handlers.py  # LoggerHandler (for agent.logs())
├── console.py   # ConsoleHandler (terminal output)
└── __init__.py  # Internal only - no public exports
```

## Internal Components

All components are internal. No public event API exports:

```python
# USER API: Just functions
def my_handler(event): pass
agent = Agent("assistant", handlers=[my_handler])

# INTERNAL: Don't import these  
from cogency.events.bus import MessageBus, emit  # Internal only
from cogency.events.handlers import LoggerHandler  # Internal only
```

**Built-in Handlers:**
- **ConsoleHandler**: Terminal output (`[INIT]`, `[TOOL]`, `[DONE]`)
- **LoggerHandler**: Structured logging for `agent.logs()`  
- **MetricsHandler**: Performance tracking

## Testing Strategy

Events can be disabled in tests:

```python
# Unit tests - focus on business logic
with patch("cogency.events.bus._bus", None):
    result = await execute_single_tool("search", {}, tools)
```

## Design Principles

**Beautiful code is minimal**: No wrapper classes, no ceremony, just functions.

**Question everything**: Eliminated complex handler hierarchies, callback interfaces, and async patterns for simple function passing.