# Agent API

```python
from cogency import Agent

# Zero ceremony
agent = Agent("assistant")
result = agent.run("What's 2+2?")

# Full configuration
agent = Agent(
    "researcher",
    max_iterations=10,             # Max reasoning iterations
    identity="You are...",         # Custom system prompt
    memory=True,                   # Enable memory
    mode="deep",                   # Reasoning mode
    notify=False                   # Disable notifications
)
```

## Parameters

- **`name`**: Agent identifier (default "cogency")
- **`tools`**: List of tool names, Tool objects, or string (default None)
- **`memory`**: Enable memory - bool or SituatedMemory instance (default False)
- **`handlers`**: Custom event handlers for streaming, websockets, etc
- **`identity`**: Custom system prompt for personality
- **`mode`**: Reasoning mode - "adapt", "fast", or "deep" (default "adapt")
- **`max_iterations`**: Max reasoning iterations (default: 10)
- **`notify`**: Enable notifications (default True)

## Methods

```python
# Execute and return complete response
result = agent.run("What's 2+2?", user_id="alice")

# Stream execution with real-time progress
async for chunk in agent.stream("Research quantum computing"):
    print(chunk, end="", flush=True)

# Get execution traces (see observability docs)
agent = Agent("assistant", handlers=[log_handler])
agent.run("Calculate something")
# Traces captured via handlers or logging
```

## Memory Configuration

```python
from cogency import Agent

# Memory is automatically configured
agent = Agent("assistant", memory=True)
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

agent = Agent("assistant")  # Tool auto-registers
```