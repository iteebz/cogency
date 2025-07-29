# Quick Start

Get up and running with Cogency in under 2 minutes.

## Installation

```bash
pip install cogency
```

## Hello World

```python
from cogency import Agent

agent = Agent("assistant")

# Simple query - thinks fast
result = await agent.run("What's 2 + 2?")
print(result)  # "4"

# Complex query - thinks deep as needed
async for chunk in agent.stream("Plan a Tokyo trip considering weather and budget"):
    print(chunk, end="", flush=True)
```

## API Keys

Create a `.env` file with any supported provider:

```bash
# Cogency auto-detects from available keys
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GEMINI_API_KEY=your-key-here
GROK_API_KEY=xai-...
MISTRAL_API_KEY=your-key-here
```

## Built-in Tools

Agents automatically discover and use built-in tools:

```python
agent = Agent("assistant")

# Uses calculator tool automatically
await agent.run("What's 15% of $1,250?")

# Uses weather tool automatically  
await agent.run("What's the weather in London?")

# Uses multiple tools for complex queries
await agent.run("Weather in Tokyo and calculate flight cost: $450 + $120 tax")
```

Available tools: Calculator, Weather, Web Search, File Manager, Shell, Code Execution, CSV/SQL processing, HTTP requests, Date/Time operations.

## Custom Tools

Create tools with zero ceremony:

```python
from cogency.tools import BaseTool, tool

@tool
class MyTool(BaseTool):
    def __init__(self):
        super().__init__("my_tool", "Does something useful", "🔧")
    
    async def run(self, param: str):
        return {"result": f"Processed: {param}"}
    
    def schema(self):
        return "my_tool(param='string')"
    
    def examples(self):
        return ["my_tool(param='hello world')"]

# Tool auto-registers - just create your agent
agent = Agent("assistant")
await agent.run("Use my_tool with hello")
```

## Memory

Agents remember conversations automatically:

```python
agent = Agent("assistant")

# Agent saves important information
await agent.run("Remember I work at Google and like Python")

# Later in conversation
await agent.run("What do you know about me?")
# "You work at Google and like Python"
```

## Output Modes

```python
# Streaming with live reasoning traces
async for chunk in agent.stream("Complex query"):
    print(chunk, end="", flush=True)

# Just the final answer
result = await agent.run("Simple query")

# Get execution traces for debugging
result = await agent.run("Query")
traces = agent.traces()  # Detailed execution log
```

## Next Steps

- Read [Cogency](cogency.md) to understand the core philosophy  
- See [Reasoning](reasoning.md) for adaptive cognitive architecture details
- Check [Tools](tools.md) for creating custom tools
- Explore [Memory](memory.md) for custom memory backends