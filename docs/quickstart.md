# Quick Start

5 minute setup.

> **v1.2.2**: Production ready with built-in tools

## Installation

```bash
pip install cogency
```

## API Key

Set any API key - Cogency auto-detects:

```bash
export OPENAI_API_KEY=sk-...
export ANTHROPIC_API_KEY=sk-ant-...
export GEMINI_API_KEY=your-key-here
export MISTRAL_API_KEY=your-key-here
```

Or use `.env` file:
```bash
OPENAI_API_KEY=sk-...
```

## Hello World

```python
from cogency import Agent

agent = Agent("assistant")
result = agent.run("What's 2 + 2?")
print(result)  # "4"
```

## Async

```python
import asyncio

async def main():
    agent = Agent("assistant")
    result = await agent.run_async("Find and summarize the latest AI research")
    print(result)

asyncio.run(main())
```

## Streaming

Real-time thinking and tool execution:

```python
import asyncio

async def main():
    agent = Agent("assistant")
    
    async for event in agent.run_stream("Analyze this complex problem"):
        if event.type == "thinking":
            print(f"💭 {event.content}")
        elif event.type == "tool_use":  
            print(f"🔧 {event.content}")
        elif event.type == "completion":
            print(f"✅ Final: {event.content}")

asyncio.run(main())
```

CLI streaming mode:
```bash
cogency --interactive --stream
```

## Built-in Tools

Auto-select relevant tools:

```python
agent.run("Calculate 15% of $1,250")  # Shell
agent.run("Latest Python 3.12 features")  # Search  
agent.run("Summarize this article: https://example.com/post")  # Scrape
agent.run("Save this data to results.json")  # Files

# Memory
agent = Agent("assistant", memory=True)
agent.run("What did I tell you about my preferences earlier?")
```

Tools auto-select based on task.

## Custom Tools

```python
from cogency.tools import Tool, tool

@tool
class MyTool(Tool):
    def __init__(self):
        super().__init__("my_tool", "Does something useful")
    
    async def run(self, args: str):
        return {"result": f"Processed: {args}"}

# Auto-registers
agent = Agent("assistant")
agent.run("Use my_tool with hello")
```

## Memory

Auto-remember conversations:

```python
agent.run("Remember I work at Google and prefer Python")
agent.run("What programming language do I prefer?")  # "Python"
```

## Adaptive Reasoning

Auto-choose thinking mode:

```python
agent.run("What's 2+2?")  # Fast mode
agent.run("Analyze this codebase and suggest improvements")  # Deep mode
```

## Configuration

```python
agent = Agent(
    "assistant",
    notify=False,       # Disable notifications
    debug=True,         # Detailed tracing
    max_iterations=20   # Reasoning iterations
)
```

## Next Steps

- **[API Reference](api.md)** - Complete documentation
- **[Tools](tools.md)** - Built-in and custom tools
- **[Examples](../examples/)** - Working applications
- **[Deployment](deployment.md)** - Production guide
- **[Memory](memory.md)** - Memory backends
- **[Reasoning](reasoning.md)** - Adaptive modes

## Common Patterns

### Research Agent
```python
agent = Agent("researcher")
agent.run("Find and analyze quantum computing research papers")
```

### Coding Assistant
```python
agent = Agent("coder")
agent.run("Create a FastAPI app with database models and run tests")
```

### Data Analysis
```python
agent = Agent("analyst")
agent.run("Process sales.csv, calculate trends, POST to dashboard")
```

---

*Ready to build? See [examples](../examples/).*