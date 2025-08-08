# Cogency

[![PyPI version](https://badge.fury.io/py/cogency.svg)](https://badge.fury.io/py/cogency)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

**A reasoning engine for adaptive AI agents.**

```python
from cogency import Agent
agent = Agent("assistant")

# Simple task → direct response
agent.run("What's 2+2?")

# Complex task → adaptive reasoning
agent.run("Analyze this codebase and suggest architectural improvements")
# Automatically escalates reasoning depth and tool usage
```

## Why Cogency?

**Zero ceremony, maximum capability** - get production-ready agents from a single import.

- **🔒 Semantic security** - Built-in safety, blocks unsafe requests automatically
- **⚡ Adaptive reasoning** - Thinks fast for simple queries, deep for complex tasks
- **🛠️ Smart tooling** - Tools auto-register and route intelligently 
- **🧠 Built-in memory** - Persistent context that actually learns about users
- **🏗️ Production ready** - Resilience, tracing, and error recovery out of the box

## Get Started in 30 Seconds

```bash
pip install cogency
export OPENAI_API_KEY=...
```

```python
from cogency import Agent

agent = Agent("assistant")
result = agent.run("What's in the current directory?")
print(result)
```

**That's it.** No configuration, no setup, no tool registration. Just working agents.

## What Makes It Different

**Semantic Security**
```python
agent.run("rm -rf /")  # ❌ Blocked automatically
agent.run("List files safely")  # ✅ Proceeds normally
```

**Adaptive Intelligence**  
```python
agent.run("What's 2+2?")  # Fast: Direct response
agent.run("Analyze my codebase")  # Deep: Multi-step reasoning
```

**Memory That Actually Works**
```python
agent = Agent("assistant", memory=True)
agent.run("I prefer Python and work at Google")
agent.run("What language should I use?")  # → "Python"
```

## Built-in Capabilities

**Tools that just work:**
📁 **Files** - Read, write, edit any file  
💻 **Shell** - Execute commands safely  
🌐 **HTTP** - API calls and requests  
📖 **Scrape** - Extract web content  
🔍 **Search** - Web search via DuckDuckGo  

**Plus add your own:**
```python
@tool
class DatabaseTool(Tool):
    async def run(self, query: str):
        return await db.execute(query)

# Automatically available to all agents
```

## Universal LLM Support

Works with any LLM - just set the API key:

```bash
# OpenAI
export OPENAI_API_KEY=sk-...

# Anthropic  
export ANTHROPIC_API_KEY=sk-ant-...

# Google Gemini
export GEMINI_API_KEY=...

# Mistral, Ollama, etc.
```

No configuration needed - Cogency detects and configures automatically.  

## Production Features

**Streaming responses:**
```python
async for chunk in agent.stream("Analyze this large codebase"):
    print(chunk, end="")
```

**Full observability:**
```python
result = agent.run("Deploy my app")
logs = agent.logs()  # See exactly what happened
print(logs)  # ["🔧 triage: selected 2 tools", "💻 shell: deploying...", ...]
```

**Error resilience:**
```python
# Tool failures don't crash execution
agent.run("List files in /nonexistent")  # → Graceful error handling
# API timeouts auto-retry with backoff
# Memory failures don't block responses
```

## Advanced Usage

```python
# Full customization when needed
agent = Agent(
    "assistant",
    memory=True,              # Persistent user context
    tools=["files", "shell"],  # Specific tools only  
    max_iterations=20,        # Deep reasoning limit
    debug=True               # Detailed execution logs
)

# Custom memory configuration
from cogency.config import MemoryConfig
agent = Agent("assistant", memory=MemoryConfig(threshold=8000))

# Custom event handlers
agent = Agent("assistant", handlers=[websocket_handler])
```

## Documentation

- **[Quick Start](docs/quickstart.md)** - Get running in 5 minutes
- **[API Reference](docs/api.md)** - Complete Agent class documentation
- **[Tools](docs/tools.md)** - Built-in tools and custom tool creation
- **[Examples](docs/examples.md)** - Detailed code examples and walkthroughs
- **[Memory](docs/memory.md)** - Memory system documentation
- **[Reasoning](docs/reasoning.md)** - Adaptive reasoning modes

## License

Apache 2.0

## Support

- **Issues**: [GitHub Issues](https://github.com/iteebz/cogency/issues)
- **Discussions**: [GitHub Discussions](https://github.com/iteebz/cogency/discussions)

*Built for developers who want agents that just work.*