# Cogency

[![PyPI version](https://badge.fury.io/py/cogency.svg)](https://badge.fury.io/py/cogency)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Downloads](https://pepy.tech/badge/cogency)](https://pepy.tech/project/cogency)

> **Conversational AI agents out of the box.**

```python
from cogency import Agent
agent = Agent("assistant")

async for chunk in agent.stream("What's the weather in Tokyo?"):
    print(chunk, end="", flush=True)
```

## 🚀 Key Features

- **🤖 Agents in 3 lines** - Fully functional, tool-using agents from a single import
- **🔥 Multistep ReAct core** - Built on explicit ReAct reasoning, not prompt spaghetti
- **🧠 Built-in memory** - Persistent memory with extensible backends (Pinecone, ChromaDB, PGVector)
- **⚡️ Zero configuration** - Auto-detects LLMs, tools, memory from environment
- **🛠️ Automatic tool discovery** - Drop tools in, they auto-register and route intelligently
- **🌊 Streaming first** - Watch agents think in real-time with full transparency
- **✨ Clean tracing** - Every reasoning step traced and streamed with clear phase indicators
- **🎭 Personality prompting** - Easily inject personality, tone, and style
- **🌍 Universal LLM support** - OpenAI, Anthropic, Gemini, Grok, Mistral out of the box
- **🧩 Extensible design** - Add tools, memory backends, embedders with zero friction
- **👥 Multi-tenancy** - Built-in user contexts and conversation history
- **🏗️ Production hardened** - Resilience, rate limiting, metrics, tracing included

## ✨ Beautiful Tracing

Watch your agents think step-by-step:

```
👤 HUMAN: Plan a 3-day Tokyo itinerary with weather considerations.

🛠️ TOOLING: web_search, weather_forecast, travel_info

🧠 REASON: Need weather forecast to plan outdoor vs indoor activities
⚡️ ACT: weather_forecast("Tokyo 3 days")
👀 OBSERVE: Day 1: sunny 25°C, Day 2: rain 18°C, Day 3: cloudy 22°C

🧠 REASON: Day 2 rain affects outdoor plans - need indoor alternatives
⚡️ ACT: travel_info("Tokyo indoor attractions museums")
👀 OBSERVE: TeamLab, Tokyo National Museum, Senso-ji Temple (covered)

🧠 REASON: Have weather + indoor options - can create complete itinerary
⚡️ ACT: Composing 3-day plan with weather-appropriate activities

🤖 AGENT: Here's your 3-day Tokyo itinerary:
Day 1 (Sunny): Shibuya, Harajuku, Meiji Shrine...
```

## ✨ Example Usage

**Basic Agent (3 lines)**
```python
import asyncio
from cogency import Agent

async def main():
    agent = Agent("assistant")
    
    async for chunk in agent.stream("What is 25 * 43?"):
        print(chunk, end="", flush=True)

asyncio.run(main())
```

**Personality Injection**
```python
# Expressive agents with personality
pirate = Agent("pirate", personality="friendly pirate who loves coding")

async for chunk in pirate.stream("Tell me about AI!"):
    print(chunk, end="", flush=True)

# Mix personality, tone, and style
teacher = Agent("teacher", personality="patient teacher", tone="encouraging", style="conversational")

async for chunk in teacher.stream("Explain quantum computing"):
    print(chunk, end="", flush=True)
```

**Multistep Reasoning**
```python
agent = Agent("travel_planner")

async for chunk in agent.stream("I'm planning a trip to London: What's the weather there? What time is it now? Flight costs $1,200, hotel is $180/night for 3 nights - total cost?"):
    print(chunk, end="", flush=True)
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
🤖 AGENT → Generate final answer
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
async for chunk in agent.stream("What's 15 * 23?"):
    print(chunk, end="", flush=True)

# 👤 HUMAN: What's 15 * 23?
# 🧠 REASON: Need to calculate 15 * 23 using calculator tool
# ⚡️ ACT: calculator(expression="15 * 23")
# 👀 OBSERVE: Result: 345
# 🤖 AGENT: The answer is 345
```

**Multi-Tenancy**
```python
# Each user gets isolated memory and conversation history
await agent.run("Remember my favorite color is blue", user_id="user1")
await agent.run("What's my favorite color?", user_id="user1")  # "blue"
await agent.run("What's my favorite color?", user_id="user2")  # No memory
```

## 🔧 Supported Providers

**LLMs** - OpenAI, Anthropic, Google, xAI, Mistral  
**Tools** - Calculator, Weather, Timezone, WebSearch, FileManager  
**Memory** - Filesystem, ChromaDB, Pinecone, PGVector  
**Embeddings** - OpenAI, Sentence Transformers, Nomic  

## 🎨 Extensibility

```python
# Custom tools auto-register
@tool
class MyTool(BaseTool):
    async def run(self, param: str):
        return {"result": f"Processed: {param}"}

# Custom memory backends
class MyMemory(MemoryBackend):
    async def memorize(self, content: str): pass
    async def recall(self, query: str): pass
```

## 📄 License

MIT - Build whatever you want.

---

**Cogency: AI agents that just work.**