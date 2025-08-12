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
result = agent.run("What's 2+2?", user_id="alice")
result = await agent.run_async("Research quantum computing")

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