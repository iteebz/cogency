# Cogency

[![PyPI version](https://badge.fury.io/py/cogency.svg)](https://badge.fury.io/py/cogency)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

**Smart AI agents that think as hard as they need to.**

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

## AdaptReAct Architecture

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

The **preprocess node** enables everything: tool selection, memory operations, and intelligent routing between reasoning modes.

## Quick Examples

**Custom Tools**

```python
from cogency.tools import BaseTool, tool

@tool
class MyTool(BaseTool):
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
# Research Agent (Perplexity-style)
agent = Agent("researcher", tools=[Search(), Scrape()])
await agent.run("Latest quantum computing developments?")

# Coding Agent (Cursor-style)
agent = Agent("coder", tools=[Files(), Shell(), Code()])
await agent.run("Fix the auth bug in this Flask app")
```

## Installation

```bash
pip install cogency
```

Set any LLM API key:

```bash
export OPENAI_API_KEY=...     # or
export ANTHROPIC_API_KEY=...  # or
export GEMINI_API_KEY=...        # etc
```

## Documentation

- **[Quick Start](docs/quickstart.md)** - Get running in 2 minutes
- **[Cogency](docs/cogency.md)** - Core breakthroughs and philosophy
- **[Reasoning](docs/reasoning.md)** - Adaptive cognitive architecture
- **[Architecture](docs/architecture.md)** - Technical implementation

## 📄 License

Apache 2.0 - Build whatever you want.

---

_Built for developers who want agents that just work, not frameworks that require PhD-level configuration._

**Cogency: A complete cognitive AI framework built from first principles in exactly 10 days using human-AI collaborative development.**
