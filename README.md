# Cogency

> **3-line AI agents that just work**

Cogency is a multistep reasoning framework that makes building AI agents stupidly simple. Auto-detects providers, intelligently routes tools, streams transparent reasoning.

## Installation

```bash
pip install cogency

# Set your API keys
echo "OPENAI_API_KEY=sk-..." >> .env
echo "ANTHROPIC_API_KEY=sk-ant-..." >> .env
echo "GEMINI_API_KEY=your-key-here" >> .env
# Agent auto-detects from any available key
```

## Quick Start

```python
import asyncio
from cogency import Agent

async def main():
    # That's it. Auto-detects LLM from .env
    agent = Agent("assistant")
    
    # Beautiful streaming ReAct reasoning
    await agent.run_streaming("What is 25 * 43?")

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

**Basic Usage** ([`examples/hello.py`](examples/hello.py))
```python
import asyncio
from cogency import Agent

async def main():
    agent = Agent("assistant")
    result = await agent.run("What is 25 * 43?")
    print(result)  # 1075

asyncio.run(main())
```

**With Tools** ([`examples/basic.py`](examples/basic.py))
```python
import asyncio
from cogency import Agent
from cogency.tools import WeatherTool

async def main():
    agent = Agent("weather_assistant", tools=[WeatherTool()])
    await agent.run_streaming("What's the weather in San Francisco?")

asyncio.run(main())
```

**Multi-Step Reasoning** ([`examples/complex.py`](examples/complex.py))
```python
import asyncio
from cogency import Agent
from cogency.tools import CalculatorTool, WeatherTool, TimezoneTool

async def main():
    agent = Agent("travel_planner", tools=[CalculatorTool(), WeatherTool(), TimezoneTool()])
    
    scenario = """
    I'm planning a trip to London. What's the weather there?
    What time is it? If my flight costs $1,200 and hotel is $180 
    per night for 3 nights, what's the total cost?
    """
    
    await agent.run_streaming(scenario)

asyncio.run(main())
```

**Custom Tools**
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

## ReAct Loop Architecture

Cogency uses a **ReAct loop** for transparent multi-step reasoning:

```
🧠 REASON → Analyze request, select tools
⚡ ACT    → Execute tools, gather results  
👀 OBSERVE → Process tool outputs
💬 RESPOND → Generate final answer
```

Every step streams in real-time and is fully traceable.

## Output Modes

**Summary Mode (Default)**: Clean final answer only
```python
result = await agent.run("What's 15 * 23?")
print(result)  # "345"
```

**Streaming**: Real-time output with beautiful formatting
```python
await agent.run_streaming("What's 15 * 23?")
# Shows live reasoning steps as they happen
```

**Stream with Modes**: Control output format
```python
async for chunk in agent.stream("Calculate something", mode="trace"):
    print(chunk, end="", flush=True)
```

**Multi-User Support**: Built-in user isolation
```python
# Each user gets isolated memory and conversation history
result = await agent.run("Remember my favorite color is blue", user_id="user1")
result = await agent.run("What's my favorite color?", user_id="user1")  # "blue"
result = await agent.run("What's my favorite color?", user_id="user2")  # No memory
```

## Supported Providers

**LLMs (Auto-detected):**
- OpenAI (GPT-4, GPT-3.5)
- Anthropic (Claude) 
- Google (Gemini)
- xAI (Grok)
- Mistral

**Built-in Tools:**
- Calculator - Math operations
- Weather - Real weather data (no API key)
- Timezone - World time (no API key)  
- WebSearch - Internet search
- FileManager - File operations

## Key Features

- **Auto-detection** - Zero config provider setup
- **Tool subsetting** - Intelligent filtering keeps prompts lean
- **Stream transparency** - Watch reasoning in real-time
- **Plug-and-play** - Drop in tools, they auto-register
- **Multi-user isolation** - Built-in user_id support for memory and conversation history

## Contributing

Framework designed for extension:

```python
# Add new tool  
class YourTool(BaseTool):
    async def run(self, **params):
        # Your implementation
```

That's it. Auto-discovery handles the rest.

## License

MIT - Build whatever you want.

---

**Cogency: AI agents out of the box.**