# Canonical Event Types

This document defines the canonical notification event types used in Cogency's phase-based execution system.

## Overview

Cogency uses a clean, phase-based notification system that maps directly to the agent's execution phases. This provides clear semantic meaning and makes it easy to understand what's happening during agent execution.

## Canonical Event Types

### Phase-Based Events

These events correspond directly to the agent's execution phases:

#### `"preprocess"`
- **When**: During preprocessing phase setup
- **Contains**: Memory extraction, tool selection, setup messages
- **Example**: `"preprocess"` → `"Saved: User mentioned working on React project"`

#### `"reason"`  
- **When**: During reasoning phase execution
- **Contains**: Thinking processes, planning, mode transitions, reflections
- **Example**: `"reason"` → `"💭 I need to search for information about React hooks"`

#### `"action"`
- **When**: During tool execution in the action phase  
- **Contains**: Tool calls, execution results, success/failure messages
- **Example**: `"action"` → `"🔍 search(query='React hooks best practices')"`

#### `"respond"`
- **When**: During response generation phase
- **Contains**: Final agent responses, response formatting
- **Example**: `"respond"` → `"🤖: Here's what I found about React hooks..."`

### System Events

#### `"trace"`
- **When**: Debug/development information (when `trace=True`)
- **Contains**: Internal state information, debug messages, system diagnostics
- **Example**: `"trace"` → `{"message": "Built tool registry with 3 tools", "phase": "preprocess"}`

## Migration from Legacy Events

The canonical system replaces these legacy event types:

- `"update"` → Replaced with phase-specific events (`"preprocess"`, `"reason"`, `"action"`, `"respond"`)
- `"state_change"` → Replaced with phase-specific events  
- `"message"` → Avoided to prevent confusion with chat messages
- Mixed content events → Clean phase-based semantic meaning

## Usage Examples

### Streaming Agent Execution

```python
agent = Agent("assistant", trace=True, verbose=True)

async for chunk in agent.stream("What's the weather?"):
    # Chunks will contain phase-based notifications:
    # preprocess: "Selected tools: weather"  
    # reason: "💭 I need to check the weather"
    # action: "🌤️ weather(location='current')"
    # respond: "🤖: The weather is sunny, 23°C"
    print(chunk)
```

### Monitoring Specific Phases

```python
# Custom callback to handle different event types
async def monitor_execution(event_type, data):
    if event_type == "reason":
        print(f"Agent thinking: {data}")
    elif event_type == "action": 
        print(f"Tool execution: {data}")
    elif event_type == "trace":
        print(f"Debug: {data}")

state.callback = monitor_execution
```

## Benefits

1. **Semantic Clarity**: Event names directly map to execution phases
2. **Debugging**: Easy to filter and monitor specific phases
3. **Consistency**: Uniform naming across the entire codebase
4. **Extensibility**: Clean foundation for future phase-based features