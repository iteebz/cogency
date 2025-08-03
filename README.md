# Cogency

[![PyPI version](https://badge.fury.io/py/cogency.svg)](https://badge.fury.io/py/cogency)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

**A reasoning engine for adaptive AI agents.**

> 🎯 **v1.0.0** - Production ready

```python
from cogency import Agent
agent = Agent("assistant")

# Simple task → direct response
agent.run("What's 2+2?")

# Complex task → adaptive reasoning
agent.run("Analyze this codebase and suggest architectural improvements")
# Automatically escalates reasoning depth and tool usage
```

## Core Concept

**Adaptive reasoning** - agents discover task complexity during execution and adjust their cognitive approach automatically.

- **Triage**: Context evaluation and tool selection
- **Reason**: Depth-adaptive thinking (fast react → deep reflection)
- **Act**: Tool execution with automatic retry and recovery
- **Respond**: Identity-aware response formatting

**Zero-cost switching** - seamless transitions preserve full context.

## Key Features

- **👌 Simple interface** - Fully functional agents from a single import
- **🔥 Adaptive reasoning** - Thinks fast or deep as needed
- **🛠️ Automatic tool discovery** - Tools auto-register and route intelligently
- **🧠 Built-in memory** - Persistent context with LLM-based synthesis
- **⚡️ Auto-configuration** - Detects LLMs and tools from environment
- **🌊 Streaming execution** - Watch agents think in real-time
- **✨ Clean tracing** - Every step traced with clear step indicators
- **🌍 Universal LLM support** - OpenAI, Anthropic, Gemini, Mistral
- **🏗️ Built-in resilience** - Automatic retry and error recovery

## How It Works

**triage → reason → act → respond**

```
👤 Build a REST API for my blog

🔧 triage: Selecting tools → files, shell
🧠 reason: Complex task → escalating to deep mode
📁 files(action='create', path='main.py') → API structure created
💻 shell(command='pip install fastapi uvicorn') → Dependencies installed
🧠 reason: Reflection → Need database integration and tests
📋 reason: Planning → Add SQLite, validation, and tests
🤖 Here's your complete FastAPI blog API...
```

## Installation

```bash
pip install cogency
```

Set any LLM API key:

```bash
export OPENAI_API_KEY=...     # or
export ANTHROPIC_API_KEY=...  # or
export GEMINI_API_KEY=...     # etc
```

## Built-in Tools

Agents automatically use relevant tools:

📁 **Files** - Create, read, edit, list files and directories  
💻 **Shell** - Execute system commands with timeout protection  
🌐 **HTTP** - API calls and web requests  
📖 **Scrape** - Intelligent web content extraction  
🔍 **Search** - Web search via DuckDuckGo  

## Quick Examples

**Custom Tools**

```python
from cogency.tools import Tool, tool

@tool
class MyTool(Tool):
    def __init__(self):
        super().__init__("my_tool", "Does something useful")

    async def run(self, args: str):
        return {"result": f"Processed: {args}"}

# Tool auto-registers
agent = Agent("assistant")
agent.run("Use my_tool with hello")
```

**Memory**

```python
# Enable memory
agent = Agent("assistant", memory=True)

# Agent remembers automatically
agent.run("I prefer Python and work at Google")
agent.run("What language should I use?")  # → "Python"
```

**Streaming**

```python
async for chunk in agent.stream("Research quantum computing"):
    print(chunk, end="", flush=True)
```

## Configuration

```python
agent = Agent(
    "assistant",
    memory=True,          # Enable memory
    debug=True,           # Detailed tracing
    max_iterations=20     # Max reasoning iterations
)
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