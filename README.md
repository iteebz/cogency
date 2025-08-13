# Cogency

[![PyPI version](https://badge.fury.io/py/cogency.svg)](https://badge.fury.io/py/cogency)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

**Adaptive AI agents that reason and act.**

```python
import asyncio
from cogency import Agent

async def main():
    agent = Agent("assistant")
    
    # Simple → fast
    result = await agent.run("What's 2+2?")
    
    # Complex → deep reasoning + tools
    result = await agent.run("Analyze this codebase and suggest improvements")
    
asyncio.run(main())
```

## Why Cogency?

**Zero ceremony. Maximum capability.**

- **🔒 Semantic security** - Blocks unsafe requests automatically
- **⚡ Adaptive reasoning** - Fast for simple, deep for complex
- **🛠️ Smart tooling** - Auto-registers and routes intelligently
- **🧠 Built-in memory** - Learns and remembers users
- **🏗️ Production ready** - Resilience, tracing, error recovery

## Get Started

```bash
pip install cogency
export OPENAI_API_KEY=...
```

```python
import asyncio
from cogency import Agent

async def main():
    agent = Agent("assistant")
    result = await agent.run("What's in the current directory?")
    print(result)

asyncio.run(main())
```

**That's it.** No configuration, no setup, just working agents.

## What Makes It Different

**Semantic Security**
```python
# Semantic security protects automatically:
await agent.run("rm -rf /")  # ❌ Blocked
await agent.run("List files safely")  # ✅ Allowed
```

**Adaptive Intelligence**  
```python
await agent.run("What's 2+2?")  # Fast
await agent.run("Analyze my codebase")  # Deep reasoning
```

**Memory That Works**
```python
agent = Agent("assistant", memory=True)
await agent.run("I prefer Python and work at Google")
await agent.run("What language should I use?")  # → "Python"
```

## Built-in Tools

📁 **Files** - Read, write, edit  
💻 **Shell** - Execute commands safely  
📖 **Scrape** - Extract web content  
🔍 **Search** - Web search  
🧠 **Retrieve** - Document embeddings  
🎯 **Recall** - Agent memory  

**Add custom tools:**
```python
@tool
class DatabaseTool(Tool):
    async def run(self, query: str):
        return await db.execute(query)
# Auto-registers with all agents
```

## Any LLM

Set any API key - Cogency auto-configures:

```bash
export OPENAI_API_KEY=sk-...
export ANTHROPIC_API_KEY=sk-ant-...
export GEMINI_API_KEY=...
export MISTRAL_API_KEY=...
export OPENROUTER_API_KEY=sk-or-v1-...
export GROQ_API_KEY=gsk_...
# Ollama: first run `ollama serve`
```  

## Production Features

**Observability:**
```python
result = await agent.run("Deploy my app")
logs = agent.logs()  # See exactly what happened
```

**Resilience:**
```python
await agent.run("List files in /nonexistent")  # Graceful errors
# Auto-retry timeouts, memory failures don't block
```

## Advanced Usage

```python
from cogency import Agent, filesystem_tools

agent = Agent(
    "assistant",
    memory=True,                    # Persistent context
    tools=filesystem_tools(),       # Specific tools
    max_iterations=20,              # Reasoning depth
    debug=True                     # Detailed logs
)

# Custom handlers
agent = Agent("assistant", handlers=[websocket_handler])
```

## Documentation

- **[Quick Start](docs/quickstart.md)** - 5 minute setup
- **[API Reference](docs/api.md)** - Complete documentation
- **[Tools](docs/tools.md)** - Built-in and custom tools
- **[Examples](examples/)** - Working applications
- **[Deployment](docs/deployment.md)** - Production guide
- **[Memory](docs/memory.md)** - Memory system
- **[Reasoning](docs/reasoning.md)** - Adaptive modes

## License

Apache 2.0

## Support

- **Issues**: [GitHub Issues](https://github.com/iteebz/cogency/issues)
- **Discussions**: [GitHub Discussions](https://github.com/iteebz/cogency/discussions)

## Tool Composition

```python
from cogency import Agent, devops_tools, research_tools, web_tools

agent = Agent("devops", tools=devops_tools())  # Files + Shell + Search
agent = Agent("researcher", tools=research_tools())  # Search + Scrape + Retrieval
agent = Agent("web", tools=web_tools())  # Search + Scrape

# Mix and match
agent = Agent("custom", tools=devops_tools() + [MyCustomTool()])
```

*Agents that just work.*