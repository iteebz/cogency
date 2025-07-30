# Cogency

[![PyPI version](https://badge.fury.io/py/cogency.svg)](https://badge.fury.io/py/cogency)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

**Smart AI agents that think as hard as they need to.**

> 🚧 **Production Beta (v0.9.0)** - Architecturally complete, actively gathering feedback from early adopters. Ready for serious evaluation and beta deployments.

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
- **⚡️ Zero configuration** - Auto-detects LLMs, tools, memory from environment
- **🧠 Built-in memory** - Persistent memory with extensible backends (Pinecone, ChromaDB, PGVector)
- **✨ Clean tracing** - Every reasoning step traced and streamed with clear phase indicators
- **🌍 Universal LLM support** - OpenAI, Anthropic, Gemini, Grok, Mistral out of the box
- **🧩 Extensible design** - Add tools, memory backends, embedders with zero friction
- **👥 Multi-tenancy** - Built-in user contexts and conversation isolation
- **🏗️ Production hardened** - Resilience, rate limiting, metrics, tracing included

## How It Works

**Preprocess → Reason → Act → Respond**

```
👤 Plan a Tokyo trip with $2000 budget

🔧 Tools: weather, calculator, search
🧠 Task complexity → escalating to Deep React
🌤️ weather(Tokyo) → 25°C sunny, rain Thu-Fri
🧮 calculator($2000 ÷ 5 days) → $400/day
🔍 search(Tokyo indoor activities) → Museums, temples
💭 Reflection: Need indoor backup plans for rainy days
📋 Planning: 5-day itinerary with weather contingencies
🤖 Here's your optimized Tokyo itinerary...
```

The preprocessing phase handles tool selection, memory operations, and intelligent routing between reasoning modes.

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
agent = Agent("researcher")
await agent.run("Latest quantum computing developments?")

# Coding Assistant
agent = Agent("coder")
await agent.run("Fix the auth bug in this Flask app")

# Data Analyst
agent = Agent("analyst")
await agent.run("Analyze sales trends in quarterly_data.csv")
```

## Built-in Tools

Agents automatically discover and use relevant tools:

🧮 **Calculator** - Mathematical expressions and calculations  
🔍 **Search** - Web search for current information  
🌤️ **Weather** - Current conditions and forecasts  
📁 **Files** - Create, read, edit, list, delete files  
💻 **Shell** - Execute system commands safely  
🐍 **Code** - Python code execution in sandboxed environment  
📊 **CSV** - Data processing and analysis  
🗄️ **SQL** - Database querying and management  
🌐 **HTTP** - Make HTTP requests with JSON parsing  
🕒 **Time** - Date/time operations and timezone conversions  
🔗 **Scrape** - Web scraping with content extraction  
🧠 **Recall** - Memory search and retrieval

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
