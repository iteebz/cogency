# Cogency

**Smart AI agents that think as hard as they need to.**

Built from frustration with boilerplate-heavy frameworks, Cogency delivers production-ready agents with zero ceremony. Drop in tools, get adaptive reasoning, watch agents think - all out of the box.

## Core Breakthroughs

### 1. Plug-and-Play Everything
```python
from cogency import Agent
agent = Agent("assistant")  # That's it. Tools, memory, reasoning - all configured.

await agent.run("What's the weather in Tokyo and cost of $450 flight + $120/night × 3?")
# Automatically uses weather and calculator tools. No setup, no config.
```

### 2. Adaptive Reasoning
```python
# Simple → Fast React (direct execution)
await agent.run("What's 2+2?")

# Complex → Deep React (reflection + planning)  
await agent.run("Analyze this codebase and suggest architectural improvements")
```

Thinks fast or deep as needed - agents discover task complexity during execution and adapt their cognitive approach automatically.

### 3. Zero-Ceremony Tool Integration
```python
from cogency.tools import BaseTool, tool

@tool
class MyTool(BaseTool):
    def __init__(self):
        super().__init__("my_tool", "Does something useful")
    
    async def run(self, param: str):
        return {"result": f"Processed: {param}"}
```

Tools auto-register and work immediately. Drop in 100 tools - the preprocess node intelligently selects what's needed.

### 4. Traceability First
Every reasoning step is traced and streamed. Not opt-in logging - intrinsic reasoning visibility:

```
👤 Plan a Tokyo trip considering weather and budget of $2000

🔧 Tools: weather, calculator, search  
🌤️ weather(Tokyo) → 25°C sunny, rain expected Thu-Fri
🧮 calculator($2000 ÷ 5 days) → $400/day budget  
🔍 search(Tokyo indoor activities rain) → Museums, shopping, temples
🧠 Day 2-3 need indoor backup plans due to rain forecast
🤖 Here's your 5-day Tokyo itinerary optimized for weather and budget...
```

## Smart Defaults, Opt-in Complexity

- **Memory**: Works out of the box with filesystem backend
- **Tools**: Auto-discovered, intelligently filtered  
- **LLM**: Auto-detects from environment (OpenAI, Anthropic, Gemini, Grok, Mistral)
- **Reasoning**: Adapts complexity automatically
- **Streaming**: First-class, not bolted-on

## AdaptReAct Architecture

**Preprocess → Reason → Act → Respond**

The preprocess node enables everything:
- **Tool subsetting**: Picks 5 relevant tools from 100 available
- **Memory operations**: Extracts and saves important information  
- **Routing decisions**: Direct response vs Fast React vs Deep React

This keeps the system extensible while maintaining performance.

## Real-World Applications

**Research Agent** (Perplexity-style):
```python
agent = Agent("researcher", tools=[Search(), Scrape()])
await agent.run("What are the latest developments in quantum computing?")
```

**Coding Agent** (Cursor-style):
```python  
agent = Agent("coder", tools=[Files(), Shell(), Code()])
await agent.run("Fix the authentication bug in this Flask app")
```

**Data Analyst**:
```python
agent = Agent("analyst", tools=[CSV(), SQL(), Calculator()])
await agent.run("Analyze sales trends and predict next quarter revenue")
```

## Philosophy

**Cognitive parsimony** - thinks as hard as needed, no more, no less. Built for developers who want agents that just work, not frameworks that require PhD-level configuration.

*An agent system that thinks fast or deep as needed and shows its work.*