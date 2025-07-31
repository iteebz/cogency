# Tools

Built-in tools auto-register and route intelligently. Create custom tools with zero ceremony.

## Built-in Tools

**Code**, **Search**, **Files**, **HTTP**, **Ask** (with memory)

```python
# Uses relevant tools automatically
await agent.run("Weather in Tokyo and calculate 15% of $1,250")
# → code(expression="1250 * 0.15")
```

## Custom Tools

```python
from cogency.tools import Tool, tool
from dataclasses import dataclass

@dataclass 
class MyToolArgs:
    query: str
    limit: int = 10

@tool  # Auto-registers
class MyTool(Tool):
    def __init__(self):
        super().__init__(
            name="my_tool",
            description="Does something useful", 
            schema="my_tool(query: str, limit: int = 10)",
            emoji="🔧",
            params=MyToolArgs,  # Auto-validation
            examples=["my_tool(query='hello', limit=5)"],
            rules=["Keep queries concise"]
        )
    
    async def run(self, query: str, limit: int = 10) -> dict:
        # Your logic here
        return {"result": f"Processed {query}"}

# Tool auto-registers - zero ceremony
agent = Agent("assistant")
await agent.run("Use my_tool with hello")
```

### Key Points
- **`@tool`** - Auto-registers with agent
- **`params=dataclass`** - Auto-validates parameters  
- **`schema`** - Explicit schema string for LLM
- **`examples/rules`** - LLM guidance
- **Return `Result.ok(data)` or `Result.fail(error)`**

## Extension Patterns

```python
# Memory-aware tool
@tool
class MemoryTool(Tool):
    def __init__(self, memory=None):
        super().__init__("memory_tool", "Searches memory")
        self.memory = memory

# API integration
@tool  
class APITool(Tool):
    def __init__(self):
        super().__init__("api", "External API calls")
        self.client = HttpClient()
        
    async def run(self, endpoint: str) -> dict:
        response = await self.client.get(endpoint)
        return {"data": response.json()}
```