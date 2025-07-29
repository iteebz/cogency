# Tools

Cogency comes with a comprehensive suite of built-in tools, plus dead-simple custom tool creation.

## Built-in Tool Suite

**🧮 Calculator** - Mathematical expressions with support for +, -, *, /, √, parentheses  
**🔍 Search** - DuckDuckGo web search for current information  
**📁 Files** - Create, read, edit, list, delete files safely within sandbox  
**🌤️ Weather** - Current conditions and forecasts for any location  
**🕒 Time** - Timezone-aware time operations and conversions  
**🌐 HTTP** - Make HTTP requests with automatic JSON parsing  
**💻 Shell** - Execute system commands with safety controls  
**🐍 Code** - Python code execution in sandboxed environment  
**📊 CSV** - Data processing and analysis of CSV files  
**🗄️ SQL** - Database querying and management  
**🧠 Recall** - Memory search and retrieval (auto-added when memory enabled)  
**🔗 Scrape** - Web scraping with content extraction

### Usage Examples

```python
agent = Agent("assistant")

# All tools auto-discovered and available
await agent.run("What's 15% of $1,250?")  # Uses Calculator
await agent.run("Weather in London?")     # Uses Weather  
await agent.run("Search for Python tutorials") # Uses Search
await agent.run("Create a file called notes.txt") # Uses Files
```

## Creating Custom Tools

### Basic Tool

```python
from cogency.tools import BaseTool, tool

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

### Tool with Memory

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

### Error Handling

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

### Using Custom Tools

```python
from cogency import Agent

# Tools auto-register, so just create your agent
agent = Agent("assistant")
from cogency.stream import stream_print
await stream_print(agent.stream("Use my_tool with hello"))

# Or specify tools explicitly
agent = Agent("assistant", tools=[MyTool(), MemoryTool()])
```

## Tool Subsetting

The preprocess node intelligently selects relevant tools:

```python
# Agent has access to all 12+ built-in tools
agent = Agent("assistant")

# But only uses what's needed for each query
await agent.run("Calculate 15 * 23")
# 🔧 Tools: calculator (1 selected from 12 available)

await agent.run("Weather in Tokyo and calculate flight cost $450 + tax $67")  
# 🔧 Tools: weather, calculator (2 selected from 12 available)
```

This keeps the system performant while maintaining extensibility.
```
