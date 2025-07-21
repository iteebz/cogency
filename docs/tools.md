# Creating Custom Tools

Tools are the building blocks that give your agent capabilities. Creating them is dead simple.

## Basic Tool

```python
from cogency.tools.base import BaseTool
from cogency.tools.registry import tool

@tool
class MyTool(BaseTool):
    def __init__(self):
        super().__init__("my_tool", "Does something useful", "🔧")
    
    async def run(self, param: str) -> dict:
        # Your tool logic here
        result = f"Processed: {param}"
        return {"result": result}
    
    def get_schema(self) -> str:
        return "my_tool(param='string')"
    
    def get_usage_examples(self) -> list:
        return ["my_tool(param='hello')"]
```

That's it. Tools auto-register and work immediately.

## Tool with Memory

Some tools need access to the agent's memory:

```python
@tool
class MemoryTool(BaseTool):
    def __init__(self, memory=None):
        super().__init__("memory_tool", "Uses memory", "🧠")
        self.memory = memory
    
    async def run(self, query: str) -> dict:
        if self.memory:
            results = await self.memory.search(query)
            return {"results": results}
        return {"error": "No memory available"}
```

## Error Handling

Tools automatically handle errors gracefully:

```python
@tool
class RiskyTool(BaseTool):
    async def run(self, data: str) -> dict:
        # If this throws an exception, it's automatically caught
        # and returned as {"error": "description", "success": False}
        risky_operation(data)
        return {"result": "success"}
```

## Using Custom Tools

```python
from cogency import Agent

# Tools auto-register, so just create your agent
agent = Agent("assistant")
from cogency.stream import stream_print
await stream_print(agent.stream("Use my_tool with hello"))

# Or specify tools explicitly
agent = Agent("assistant", tools=[MyTool(), MemoryTool()])
```