# Cogency

> **3-line AI agents that just work**

Cogency is a multistep reasoning framework that makes building AI agents stupidly simple. Auto-detects providers, intelligently routes tools, streams transparent reasoning.

## Installation

```bash
# Current broken until next release v0.3.1 (pending)
# Recommended: Fork and install from source
pip install cogency
```

## Quick Start

```python
import asyncio
from cogency import Agent

async def main():
    # That's it. Auto-detects LLM from .env
    agent = Agent("assistant")
    result = await agent.run("What is 25 * 43?")
    print(result)

asyncio.run(main())
```

**Requirements:** Python 3.9+, API key in `.env`

## Core Philosophy

- **Zero ceremony** - 3 lines to working agent
- **Magical auto-detection** - Detects OpenAI, Anthropic, Gemini, Grok, Mistral from environment
- **Intelligent tool routing** - LLM filters relevant tools, keeps prompts lean
- **Stream-first** - Watch agents think in real-time
- **Plug-and-play** - Drop in new tools, they just work

## Examples

### Hello World
```python
import asyncio
from cogency import Agent

async def main():
    agent = Agent("assistant")
    result = await agent.run("What is 25 * 43?")
    print(result)  # 1075

asyncio.run(main())
```

### With Tools
```python
import asyncio
from cogency import Agent, WeatherTool

async def main():
    agent = Agent("weather_assistant", tools=[WeatherTool()])
    result = await agent.run("What's the weather in San Francisco?")
    print(result)

asyncio.run(main())
```

### Streaming Reasoning
```python
import asyncio
from cogency import Agent, CalculatorTool, WebSearchTool

async def main():
    agent = Agent("analyst", tools=[CalculatorTool(), WebSearchTool()])

    async for chunk in agent.stream("Find Bitcoin price and calculate value of 0.5 BTC"):
        if chunk["type"] == "thinking":
            print(f"💭 {chunk['content']}")
        elif chunk["type"] == "tool_call":  
            print(f"🔧 {chunk['content']}")
        elif chunk["type"] == "result":
            print(f"✅ {chunk['data']}")

asyncio.run(main())
```

### Custom Tools
```python
from cogency import Agent, BaseTool

class TimezoneTool(BaseTool):
    def __init__(self):
        super().__init__("timezone", "Get time in any city")
    
    async def run(self, city: str):
        return {"time": f"Current time in {city}: 14:30 PST"}
    
    def get_schema(self):
        return "timezone(city='string')"

agent = Agent("time_assistant", tools=[TimezoneTool()])
```

## Installation

```bash
pip install cogency

# Set your API keys
echo "OPENAI_API_KEY=sk-..." >> .env
echo "ANTHROPIC_API_KEY=sk-ant-..." >> .env
echo "GEMINI_API_KEY=your-key-here" >> .env
# Agent auto-detects from any available key
```

## Supported Providers

**LLMs (Auto-detected):**
- OpenAI (GPT-4, GPT-3.5)
- Anthropic (Claude) 
- Google (Gemini)
- xAI (Grok)
- Mistral

**Embeddings (Auto-detected):**
- OpenAI (text-embedding-3)
- Nomic (nomic-embed-text)
- Sentence Transformers (local)

**Built-in Tools:**
- Calculator - Math operations
- Weather - Real weather data (no API key)
- Timezone - World time (no API key)  
- WebSearch - Internet search
- FileManager - File operations

## PRARR Architecture

Cogency uses **Plan-Reason-Act-Reflect-Respond** for transparent multi-step reasoning:

```
📋 PLAN    → Analyze request, filter relevant tools
🧠 REASON  → Determine tool usage strategy  
⚡ ACT     → Execute tools, gather results
🔍 REFLECT → Filter out bullshit, focus results
💬 RESPOND → Generate clean final answer
```

Every step is streamable and traceable.

## Beautiful Tracing

```python
import asyncio
from cogency import Agent, CalculatorTool

async def main():
    agent = Agent("analyst", tools=[CalculatorTool()])
    result = await agent.run("What's 15 * 23?")
    print(result)

asyncio.run(main())

# Automatic beautiful traces
🚀 EXECUTION TRACE (450ms total)
==================================================
🔸 PLAN [14:30:15] 120ms
   📥 'What's 15 * 23?'
   📤 Decision: tool_needed

🔸 REASON [14:30:15] 80ms  
   📥 executed
   📤 completed

🔸 ACT [14:30:15] 200ms
   📥 executed  
   📤 completed

🔸 REFLECT [14:30:15] 50ms
   📥 executed
   📤 completed
==================================================
✅ Complete in 450ms
```

## Key Features

- **Auto-detection** - Zero config provider setup
- **Tool subsetting** - Intelligent filtering keeps prompts lean
- **Key rotation** - Load balance across multiple API keys
- **Result filtering** - Remove execution metadata in REFLECT
- **Stream transparency** - Watch reasoning in real-time
- **Beautiful traces** - Human-readable execution logs
- **Plug-and-play** - Drop in tools, they auto-register

## Contributing

Framework designed for extension:

```python
# Add new LLM provider
class YourLLM(ProviderMixin, BaseLLM):
    async def invoke(self, messages, **kwargs):
        # Your implementation
        
# Add new tool  
class YourTool(BaseTool):
    async def run(self, **params):
        # Your implementation
```

That's it. Auto-discovery handles the rest.

## License

MIT - Build whatever you want.

---

**Cogency: AI agents without the ceremony.**