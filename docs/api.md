# Agent API

```python
from cogency import Agent, devops_tools

agent = Agent("assistant")
result = agent.run("What's 2+2?")

# With tools
agent = Agent("assistant", tools=devops_tools())

# Full config
agent = Agent(
    "researcher",
    tools=devops_tools(),          # Tool helpers
    max_iterations=10,             # Reasoning limit
    identity="You are...",         # Custom prompt
    memory=True,                   # Enable memory
    notify=False                   # Disable notifications
)
```

## Parameters

- **`name`**: Agent identifier (default "cogency")
- **`tools`**: Tool objects or helpers (default None)
- **`memory`**: Enable memory - bool or ProfileManager (default False)
- **`handlers`**: Event handlers for streaming, websockets, etc
- **`identity`**: Custom system prompt
- **`max_iterations`**: Max reasoning iterations (default: 10)
- **`notify`**: Enable notifications (default True)

## Methods

```python
# Synchronous execution
result = agent.run("What's 2+2?", user_id="alice")

# Asynchronous execution
result = await agent.run_async("Research quantum computing")

# Streaming execution (real-time thinking + output)
async for event in agent.run_stream("Complex research task"):
    if event.type == "thinking":
        print(f"💭 {event.content}")
    elif event.type == "tool_use":
        print(f"🔧 {event.content}")
    elif event.type == "completion":
        print(f"✅ {event.content}")

# Execution traces
agent = Agent("assistant", handlers=[log_handler])
agent.run("Calculate something")
# Traces via handlers or logging
```

## Memory

```python
agent = Agent("assistant", memory=True)  # Auto-configured
```

## Custom Tools

```python
from cogency.tools import Tool, tool

@tool
class CustomTool(Tool):
    def __init__(self):
        super().__init__("custom", "Custom functionality")
    
    async def run(self, args: str) -> dict:
        return {"result": f"Processed: {args}"}

agent = Agent("assistant")  # Auto-registers
```

## Streaming

Real-time execution with intermediate thinking and tool usage updates:

```python
# Async streaming (recommended)
async for event in agent.run_stream("Complex analysis task"):
    print(f"{event.type}: {event.content}")

# Event types:
# - "thinking": Intermediate reasoning steps
# - "tool_use": Tool execution progress  
# - "completion": Final result
# - "error": Error conditions

# CLI streaming mode
# cogency --interactive --stream
```

### Stream Event Structure

```python
@dataclass
class StreamEvent:
    type: str        # Event category
    content: str     # Human-readable content
    metadata: dict   # Additional event data
```

### Streaming Benefits

- **Real-time feedback**: See reasoning progress as it happens
- **Tool transparency**: Watch tool execution in real-time
- **Better UX**: No waiting for long-running tasks
- **Zero overhead**: Built on existing event system
- **Interruptible**: Can handle cancellation gracefully