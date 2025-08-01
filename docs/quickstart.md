# Quick Start

Get up and running with Cogency in 5 minutes.

> 🚧 **Beta Notice**: This is production beta software (v0.9.0). Core functionality is stable, but edge cases in cross-provider behavior and memory backends are still being addressed.

## Installation

```bash
pip install cogency
```

## API Key Setup

Cogency auto-detects your LLM provider. Set any supported API key:

```bash
# OpenAI
export OPENAI_API_KEY=sk-...

# Anthropic  
export ANTHROPIC_API_KEY=sk-ant-...

# Google Gemini
export GEMINI_API_KEY=your-key-here


# Mistral
export MISTRAL_API_KEY=your-key-here
```

Or create a `.env` file:
```bash
OPENAI_API_KEY=sk-...
```

## Hello World

```python
from cogency import Agent

# Create an agent
agent = Agent("assistant")

# Simple query
result = await agent.run("What's 2 + 2?")
print(result)  # "4"
```

## Streaming Execution

Watch your agent think in real-time:

```python
async for chunk in agent.stream("What's the weather in London?"):
    print(chunk, end="", flush=True)
```

Output:
```
🌤️ weather(location='London') → sunny, 18°C
The weather in London is currently sunny with a temperature of 18°C.
```

## Built-in Tools

Agents automatically use relevant tools:

```python
# Uses code tool
await agent.run("What's 15% of $1,250?")

# Uses weather tool  
await agent.run("Weather in Tokyo?")

# Uses multiple tools
await agent.run("Weather in Paris and calculate 450 EUR to USD")
```

Available tools: Code, Web Search, Files, HTTP, Ask.

## Custom Tools

Create tools with minimal code:

```python
from cogency.tools import Tool, tool

@tool
class MyTool(Tool):
    def __init__(self):
        super().__init__("my_tool", "Does something useful")
    
    async def run(self, param: str):
        return {"result": f"Processed: {param}"}

# Tool auto-registers - just create your agent
agent = Agent("assistant")
await agent.run("Use my_tool with hello")
```

## Memory

Agents remember conversations automatically:

```python
# Agent saves important information
await agent.run("Remember I work at Google and prefer Python")

# Later in the conversation
await agent.run("What programming language do I prefer?")
# "You prefer Python"
```

## Adaptive Reasoning

Agents automatically choose the right thinking mode:

```python
# Simple query → fast mode
await agent.run("What's 2+2?")

# Complex query → deep mode with reflection and planning
await agent.run("Analyze this codebase and suggest improvements")
```

## Configuration

```python
# Custom configuration
agent = Agent(
    "assistant",
    mode="deep",        # Force deep reasoning
    notify=False,       # Disable progress notifications
    debug=True,         # Enable detailed tracing
    depth=20           # Allow more reasoning iterations
)
```

## Next Steps

- **[API Reference](api.md)** - Complete Agent class documentation
- **[Tools](tools.md)** - Built-in tools and custom tool creation  
- **[Examples](examples.md)** - Detailed code examples
- **[Memory](memory.md)** - Memory backends and configuration
- **[Reasoning](reasoning.md)** - Understanding adaptive reasoning modes

## Common Patterns

### Research Agent
```python
agent = Agent("researcher")
result = await agent.run("What are the latest developments in quantum computing?")
```

### Coding Assistant
```python
agent = Agent("coder")
result = await agent.run("Write a Python function to calculate Fibonacci numbers")
```

### Data Analysis
```python
agent = Agent("analyst")  
result = await agent.run("Analyze the sales data in data.csv and find trends")
```

---

*Ready to build? Check out the [examples](examples.md) for more detailed walkthroughs.*