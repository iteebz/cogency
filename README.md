# Cogency

[![PyPI version](https://badge.fury.io/py/cogency.svg)](https://badge.fury.io/py/cogency)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

**Smart AI agents that think as hard as they need to.**

> 🎆 **v1.0.0 Release** - Production ready with canonical 5-tool architecture. Clean, minimal, complete.

```python
from cogency import Agent
agent = Agent("assistant")

# Simple task → thinks fast
await agent.run("What's 2+2?")

# Complex task → thinks deep
await agent.run("Analyze this codebase and suggest architectural improvements")
# Automatically escalates reasoning, uses relevant tools, streams thinking
```

## 🧠 Adaptive Reasoning

**Thinks fast or deep as needed** - agents discover task complexity during execution and adapt their cognitive approach automatically.

- **Fast React**: Direct execution for simple queries
- **Deep React**: Reflection + planning for complex analysis
- **Zero-cost switching**: Seamless transitions preserve full context
- **Runtime discovery**: No upfront classification - intelligence governs intelligence

## 🚀 Key Features

- **🤖 Agents in 3 lines** - Fully functional, tool-using agents from a single import
- **🔥 Adaptive reasoning** - Thinks fast or deep as needed, switches seamlessly during execution
- **🌊 Streaming first** - Watch agents think in real-time with full transparency
- **🛠️ Automatic tool discovery** - Drop tools in, they auto-register and route intelligently
- **⚡️ Zero configuration** - Auto-detects LLMs, tools, memory from environment (fast models by default)
- **🧠 Built-in memory** - Persistent memory with extensible backends (Pinecone, ChromaDB, PGVector)
- **✨ Clean tracing** - Every reasoning step traced and streamed with clear phase indicators
- **🌍 Universal LLM support** - OpenAI, Anthropic, Gemini, Grok, Mistral out of the box
- **🧩 Extensible design** - Add tools, memory backends, embedders with zero friction
- **👥 Multi-tenancy** - Built-in user contexts and conversation isolation
- **🏗️ Production hardened** - Resilience, rate limiting, metrics, tracing included

## How It Works

**Prepare → Reason → Act → Respond**

```
👤 Build a REST API for my blog

🔧 Tools: files, shell, search
🧠 Task complexity → escalating to Deep React
🔍 search(query='FastAPI best practices') → 5 results
📖 scrape(url='fastapi.tiangolo.com/tutorial') → FastAPI Tutorial
📁 files(action='create', path='main.py') → API structure created
💻 shell(command='pip install fastapi uvicorn') → Dependencies installed
💭 Reflection: Need database integration and error handling
📋 Planning: Add SQLite, validation, and tests
🤖 Here's your complete FastAPI blog API...
```

The preparing phase handles tool selection, memory operations, and intelligent routing between reasoning modes.

## Quick Examples

**Custom Tools**

```python
from cogency.tools import Tool, tool

@tool
class MyTool(Tool):
    def __init__(self):
        super().__init__("my_tool", "Does something useful")

    async def run(self, param: str):
        return {"result": f"Processed: {param}"}

# Tool auto-registers - just create agent
agent = Agent("assistant")
await agent.run("Use my_tool with hello")
```

**Real-World Applications**

```python
# Research Agent
agent = Agent("researcher", tools=["search", "scrape"])
await agent.run("Latest quantum computing developments?")

# Coding Assistant
agent = Agent("coder", tools=["files", "shell"])
await agent.run("Build a FastAPI service with database integration")

# Data Analyst
agent = Agent("analyst", tools=["files", "shell", "http"])
await agent.run("Process this CSV and POST results to analytics API")
```

## Canonical 5 Tools

Agents automatically discover and use relevant tools:

📁 **Files** - Create, read, edit, list files and directories  
💻 **Shell** - Execute system commands safely with timeout protection  
🌐 **HTTP** - Universal network primitive for API calls and web requests  
📖 **Scrape** - Intelligent web content extraction with clean text output  
🔍 **Search** - Web search for current information via DuckDuckGo  

**Complete primitive coverage** - These 5 tools compose to handle any reasonable AI agent task. HTTP serves as the universal fallback when specialized abstractions don't exist.

## Installation

```bash
pip install cogency
```

**Beta Note**: Cross-provider testing is ongoing. OpenAI and Anthropic are well-tested; other providers may have edge cases.

Set any LLM API key:

```bash
export OPENAI_API_KEY=...     # or
export ANTHROPIC_API_KEY=...  # or
export GEMINI_API_KEY=...        # etc
```

## Documentation

- **[Quick Start](docs/quickstart.md)** - Get running in 5 minutes
- **[API Reference](docs/api.md)** - Complete Agent class documentation
- **[Tools](docs/tools.md)** - Built-in tools and custom tool creation
- **[Examples](docs/examples.md)** - Detailed code examples and walkthroughs
- **[Memory](docs/memory.md)** - Memory backends and configuration
- **[Reasoning](docs/reasoning.md)** - Adaptive reasoning modes
- **[Configuration](docs/configuration.md)** - Advanced configuration options
- **[Troubleshooting](docs/troubleshooting.md)** - Common issues and solutions

## 📄 License

Apache 2.0 - Build whatever you want.

## Beta Feedback

We're actively gathering feedback from early adopters:

- **Issues**: [GitHub Issues](https://github.com/iteebz/cogency/issues)
- **Discussions**: [GitHub Discussions](https://github.com/iteebz/cogency/discussions)
- **Known limitations**: Cross-provider behavior, memory backend edge cases

---

_Built for developers who want agents that just work, not frameworks that require PhD-level configuration._
