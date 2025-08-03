# Examples

## Basics

```python
from cogency import Agent

agent = Agent("assistant")
result = agent.run("What's 2+2?")  # → "4"

# Streaming
async for chunk in agent.stream("Weather in London?"):
    print(chunk, end="", flush=True)
# → 🔍 search(query="London weather") → sunny, 18°C
```

## Real-World Applications

### Research Agent
```python
from cogency import Agent

# Create a research-focused agent
agent = Agent("researcher")

# Deep research query
query = """
Research the current state of renewable energy adoption globally. 
Include statistics, recent developments, and major challenges.
Create a summary report.
"""

async for chunk in agent.stream(query):
    print(chunk, end="", flush=True)
```

### Coding Assistant
```python
agent = Agent("coder")

# Code generation
agent.run("Write a Python function to calculate Fibonacci numbers efficiently")

# Code analysis
agent.run("Review this Python code and suggest improvements: [paste code here]")

# Debugging help
agent.run("This code is throwing a KeyError. Help me debug it: [paste code]")
```

### Data Analyst
```python
agent = Agent("analyst")

# Data analysis
agent.run("Analyze the sales data in quarterly_sales.csv and identify trends")

# Report generation
agent.run("""
Load customer_data.csv, analyze customer segments, 
and create a summary report with key insights
""")
```

## Memory Examples

### Persistent Conversations
```python
agent = Agent("assistant", memory=True)

# First conversation
agent.run("Remember that I work at Google and I'm working on a React project")

# Later conversation
agent.run("What project am I working on?")
# "You're working on a React project at Google"
```

## Custom Tool Examples

### API Integration Tool
```python
from cogency.tools import Tool, tool

@tool
class WeatherAPI(Tool):
    def __init__(self):
        super().__init__("weather_api", "Get weather from custom API")
    
    async def run(self, city: str, country: str = "US") -> dict:
        # Make API call
        return {"temperature": 25, "condition": "sunny"}

agent = Agent("assistant")  # Tool auto-registers
```

### Database Tool
```python
@tool
class DatabaseQuery(Tool):
    def __init__(self, db_connection):
        super().__init__("database", "Query the database")
        self.db = db_connection
    
    async def run(self, query: str, limit: int = 100) -> dict:
        # Execute database query
        return {"results": [], "success": True}

agent = Agent("assistant")
```

## Configuration Examples

### Development Configuration
```python
agent = Agent(
    "dev-agent",
    debug=True,
    notify=True,
    max_iterations=5
)
```

### Production Configuration
```python
agent = Agent(
    "production-agent",
    memory=True,
    notify=False
)
```

### Specialized Agent
```python
agent = Agent(
    "researcher",
    max_iterations=20,
    identity="You are a thorough researcher who cites sources."
)
```

## Error Handling Examples

### Basic Error Handling
```python
try:
    result = agent.run("Complex query that might fail")
    print(result)
except Exception as e:
    print(f"Agent execution failed: {e}")
```

### Custom Error Recovery
```python
import asyncio

async def safe_agent_run(agent, query, max_retries=3):
    for attempt in range(max_retries):
        try:
            return agent.run(query)
        except Exception as e:
            if attempt == max_retries - 1:
                return f"Failed after {max_retries} attempts: {e}"
            await asyncio.sleep(2 ** attempt)  # Exponential backoff

result = await safe_agent_run(agent, "Complex query")
```

## Integration Examples

### FastAPI Integration
```python
from fastapi import FastAPI
from cogency import Agent

app = FastAPI()
agent = Agent("api-assistant")

@app.post("/chat")
async def chat(query: str):
    result = agent.run(query)
    return {"response": result}
```

### Discord Bot Integration
```python
import discord
from cogency import Agent

agent = Agent("discord-bot")

class CogencyBot(discord.Client):
    async def on_message(self, message):
        if message.content.startswith('!ask'):
            query = message.content[5:]
            response = agent.run(query)
            await message.channel.send(response)

bot = CogencyBot()
```

## Performance Examples

### Batch Processing
```python
import asyncio

agent = Agent("batch-processor")

async def process_batch(queries):
    tasks = [agent.run(query) for query in queries]
    return await asyncio.gather(*tasks)

queries = ["Analyze sales data", "Generate report"]
results = await process_batch(queries)
```

---

*These examples demonstrate the flexibility and power of Cogency for various use cases. Adapt them to your specific needs.*