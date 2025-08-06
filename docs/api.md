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
    identity="You are...", # Custom system prompt
    memory=True,          # Enable memory
    debug=True            # Detailed logging
)
```

## Parameters

- **`max_iterations`**: Max reasoning iterations (default: 10)
- **`identity`**: Custom system prompt for personality
- **`memory`**: Enable memory (bool or MemoryConfig)
- **`debug`**: Detailed execution tracing
- **`tools`**: List of tools or "all" for full access
- **`notify`**: Enable notifications (default True)

## Methods

```python
# Execute and return complete response
result = agent.run("What's 2+2?", user_id="alice")

# Stream execution with real-time progress
async for chunk in agent.stream("Research quantum computing"):
    print(chunk, end="", flush=True)

# Get execution traces (debug mode only)
agent = Agent(debug=True)
agent.run("Calculate something")
logs = agent.logs(mode="debug")  # List of execution details
```

## Memory Configuration

```python
from cogency import Agent, MemoryConfig

# Custom memory config
memory_config = MemoryConfig(
    synthesis_threshold=8000,
    user_id="specific_user"
)

agent = Agent("assistant", memory=memory_config)
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