# Cogency

[![PyPI version](https://badge.fury.io/py/cogency.svg)](https://badge.fury.io/py/cogency)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Downloads](https://pepy.tech/badge/cogency)](https://pepy.tech/project/cogency)

> **3-line AI agents that just work**

```python
from cogency import Agent
agent = Agent("assistant")
await agent.run_streaming("What's the weather in Tokyo?")
```

## ✨ Jaw-Dropping Features

- **🤖 Agents in 3 lines** - Fully functional, tool-using agents from a single import
- **🔥 ReAct core** - Built on explicit ReAct reasoning, not prompt spaghetti
- **🧠 Built-in memory** - Persistent memory with extensible backends (ChromaDB, Pinecone, PGVector)
- **⚡️ Zero configuration** - Auto-detects LLMs, tools, memory from environment
- **🧬 Multi-step reasoning** - Transparent think → act → observe → respond loops
- **🌊 Streaming first** - Watch agents think in real-time with full transparency
- **✨ Clean tracing** - Every reasoning step traced and streamed with clear phase indicators
- **🎭 Expressive personalities** - `Agent("pirate", personality="friendly pirate who codes")`
- **🛠️ Automatic tool discovery** - Drop tools in, they auto-register and route intelligently
- **🌍 Universal LLM support** - OpenAI, Anthropic, Gemini, Grok, Mistral out of the box
- **🧩 Extensible design** - Add tools, memory backends, LLMs with zero friction
- **👥 Multi-tenancy** - Built-in user contexts and conversation history
- **🏗️ Production ready** - Resilience, rate limiting, metrics, tracing included

## ✨ Beautiful API Examples

**Basic Agent (3 lines)**
```python
import asyncio
from cogency import Agent

async def main():
    agent = Agent("assistant")
    await agent.run_streaming("What is 25 * 43?")

asyncio.run(main())
```

**Personality Injection**
```python
# Expressive agents with personality
pirate = Agent("pirate", personality="friendly pirate who loves coding")
await pirate.run_streaming("Tell me about AI!")

# Mix personality, tone, and style
teacher = Agent("teacher", personality="patient teacher", tone="encouraging", style="conversational")
await teacher.run_streaming("Explain quantum computing")
```

**Multistep Reasoning**
```python
agent = Agent("travel_planner")
await agent.run_streaming("""
    I'm planning a trip to London:
    1. What's the weather there?
    2. What time is it now?
    3. Flight costs $1,200, hotel is $180/night for 3 nights - total cost?
""")
```

**Custom Tools (Auto-Discovery)**
```python
from cogency import Agent, BaseTool

class TimezoneTool(BaseTool):
    def __init__(self):
        super().__init__("timezone", "Get time in any city")
    
    async def run(self, city: str):
        return {"time": f"Current time in {city}: 14:30 PST"}
    
    def get_schema(self):
        return "timezone(city='string')"

# Just create agent - tool auto-registers
agent = Agent("time_assistant", tools=[TimezoneTool()])
```

**Memory Backends**
```python
from cogency import Agent, FSMemory
from cogency.memory.backends import ChromaDB, Pinecone, PGVector

# Built-in filesystem memory
agent = Agent("memory_agent", memory=FSMemory())

# Vector databases
agent = Agent("vector_agent", memory=ChromaDB())
agent = Agent("cloud_agent", memory=Pinecone(api_key="...", index="my-index"))
```

## 🧠 ReAct Loop Architecture

Cogency uses transparent **ReAct loops** for multistep reasoning:

```
🧠 REASON → Analyze request, select tools
⚡️ ACT    → Execute tools, gather results  
👀 OBSERVE → Process tool outputs
💬 RESPOND → Generate final answer
```

Every step streams in real-time and is fully traceable.

## 📦 Installation

### Quick Start
```bash
pip install cogency
echo "OPENAI_API_KEY=sk-..." >> .env  # or any supported provider
```

### With All Features
```bash
pip install cogency[all]  # All LLMs, embeddings, memory backends
```

### Selective Installation
```bash
# LLM providers
pip install cogency[openai]      # OpenAI GPT models
pip install cogency[anthropic]   # Claude models  
pip install cogency[gemini]      # Google Gemini
pip install cogency[mistral]     # Mistral AI

# Memory backends  
pip install cogency[chromadb]    # ChromaDB vector store
pip install cogency[pgvector]    # PostgreSQL with pgvector
pip install cogency[pinecone]    # Pinecone vector store

# Embedding providers
pip install cogency[sentence-transformers]  # Local embeddings
pip install cogency[nomic]                  # Nomic embeddings
```

## 🎯 Output Modes

**Summary Mode (Default)**
```python
result = await agent.run("What's 15 * 23?")
print(result)  # "345"
```

**Beautiful Streaming**
```python
await agent.run_streaming("What's 15 * 23?")
# 🧠 REASON → Let me calculate 15 * 23 using the calculator tool
# ⚡️ ACT    → calculator(expression="15 * 23")
# 👀 OBSERVE → Result: 345
# 💬 RESPOND → The answer is 345
```

**Multi-Tenancy**
```python
# Each user gets isolated memory and conversation history
await agent.run("Remember my favorite color is blue", user_id="user1")
await agent.run("What's my favorite color?", user_id="user1")  # "blue"
await agent.run("What's my favorite color?", user_id="user2")  # No memory
```

## 🔧 Supported Providers

**LLMs (Auto-detected from .env)**
- OpenAI (GPT-4, GPT-3.5)
- Anthropic (Claude) 
- Google (Gemini)
- xAI (Grok)
- Mistral

**Built-in Tools**
- Calculator - Math operations
- Weather - Real weather data (no API key)
- Timezone - World time (no API key)  
- WebSearch - Internet search
- FileManager - File operations

**Memory Backends**
- FilesystemBackend - Local JSON storage
- ChromaDB - Vector database
- Pinecone - Cloud vector store
- PGVector - PostgreSQL with vectors

**Embedding Providers**
- OpenAI - text-embedding-3-large
- Sentence Transformers - Local embeddings
- Nomic - Nomic embeddings

## 🏗️ Production Features

**Resilience**
```python
# Built-in rate limiting, circuit breakers, retries
agent = Agent("production_agent", 
              enable_mcp=True,          # MCP server support
              conversation_history=True, # Multi-turn conversations
              trace=True)               # Full execution tracing
```

**Metrics & Monitoring**
```python
# OpenTelemetry integration
from cogency.core.metrics import get_metrics
metrics = get_metrics()  # Execution time, token usage, tool calls
```

## 🎨 Extensibility

**Custom Tools**
```python
from cogency.tools.registry import tool

@tool
class MyTool(BaseTool):
    async def run(self, param: str):
        return {"result": f"Processed: {param}"}
    
    def get_schema(self):
        return "my_tool(param='string')"

# Auto-registers with all agents
```

**Custom Memory Backends**
```python
from cogency.memory.core import MemoryBackend

class MyMemoryBackend(MemoryBackend):
    async def memorize(self, content: str, metadata: dict = None):
        # Your implementation
        pass
    
    async def recall(self, query: str, limit: int = 5):
        # Your implementation
        pass
```

**Custom LLM Providers**
```python
from cogency.llm.base import BaseLLM

class MyLLM(BaseLLM):
    async def invoke(self, messages: list):
        # Your implementation
        pass
```

## 🔍 Advanced Usage

**System Prompts**
```python
# Direct system prompt override
agent = Agent("assistant", system_prompt="You are a helpful coding assistant")

# Composable personality + tone + style
agent = Agent("writer", 
              personality="creative writer",
              tone="inspiring", 
              style="narrative")
```

**Tool Subsetting**
```python
# Agent intelligently filters relevant tools per query
agent = Agent("smart_agent", tools=[
    CalculatorTool(), WeatherTool(), TimezoneTool(), 
    WebSearchTool(), FileManagerTool()
])
# Only relevant tools are included in LLM context
```

**Memory Integration**
```python
# Memory auto-extracts during pre-react phase
agent = Agent("memory_agent", memory=ChromaDB())
await agent.run("I love pizza")
await agent.run("What do I like to eat?")  # Recalls "pizza"
```

## 🤝 Contributing

Framework designed for extension:

```python
# Add new tool  
class YourTool(BaseTool):
    async def run(self, **params):
        # Your implementation
        pass

# Add new memory backend
class YourMemory(MemoryBackend):
    async def memorize(self, content: str):
        # Your implementation
        pass

# Add new LLM provider
class YourLLM(BaseLLM):
    async def invoke(self, messages: list):
        # Your implementation
        pass
```

That's it. Auto-discovery handles the rest.

## 📄 License

MIT - Build whatever you want.

---

**Cogency: AI agents that just work.**