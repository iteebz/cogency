# Quick Start

Get up and running with Cogency in 5 minutes.

> 🎯 **v1.0.0**: Production ready with canonical 5-tool architecture

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
result = agent.run("What's 2 + 2?")
print(result)  # "4"
```

## Streaming Execution

Watch your agent think in real-time:

```python
async for chunk in agent.stream("Find and summarize the latest AI research"):
    print(chunk, end="", flush=True)
```

Output:
```
🔍 search(query='latest AI research 2024') → 5 results
📖 scrape(url='https://arxiv.org/recent') → Recent AI Papers
Based on recent research, key developments include improved transformer architectures and multimodal AI advances.
```

## Built-in Tools

Agents automatically use relevant tools:

```python
# Uses shell tool for computation
agent.run("Calculate 15% of $1,250")

# Uses search tool for current information
agent.run("Latest Python 3.12 features")

# Uses scrape tool for content extraction
agent.run("Summarize this article: https://example.com/post")

# Uses files tool for data persistence
agent.run("Save this data to results.json")

# Uses http tool for API calls
agent.run("Get my GitHub profile via API")
```

Tools automatically selected based on task requirements.

## Custom Tools

Create tools with minimal code:

```python
from cogency.tools import Tool, tool

@tool
class MyTool(Tool):
    def __init__(self):
        super().__init__("my_tool", "Does something useful")
    
    async def run(self, args: str):
        return {"result": f"Processed: {args}"}

# Tool auto-registers - just create your agent
agent = Agent("assistant")
agent.run("Use my_tool with hello")
```

## Memory

Agents remember conversations automatically:

```python
# Agent saves important information
agent.run("Remember I work at Google and prefer Python")

# Later in the conversation
agent.run("What programming language do I prefer?")
# "You prefer Python"
```

## Adaptive Reasoning

Agents automatically choose the right thinking mode:

```python
# Simple query → fast mode
agent.run("What's 2+2?")

# Complex query → deep mode with reflection and planning
agent.run("Analyze this codebase and suggest improvements")
```

## Configuration

```python
# Custom configuration
agent = Agent(
    "assistant",
    notify=False,       # Disable progress notifications
    debug=True,         # Enable detailed tracing
    max_iterations=20   # Allow more reasoning iterations
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
from cogency import Agent

# Tools auto-register - agents use what they need
agent = Agent("researcher")
result = agent.run("Find and analyze the latest quantum computing research papers")
```

### Coding Assistant
```python
from cogency import Agent

# Built-in tools: Files, Shell, HTTP, Search, Scrape
agent = Agent("coder")
result = agent.run("Create a FastAPI app with database models and run tests")
```

### Data Analysis
```python
from cogency import Agent

# All tools available automatically
agent = Agent("analyst")
result = agent.run("Process sales.csv, calculate trends, and POST to dashboard API")
```

---

*Ready to build? Check out the [examples](examples.md) for more detailed walkthroughs.*