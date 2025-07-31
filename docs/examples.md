# Examples

## Basics

```python
from cogency import Agent

agent = Agent("assistant")
result = await agent.run("What's 2+2?")  # → "4"

# Streaming
async for chunk in agent.stream("Weather in London?"):
    print(chunk, end="", flush=True)
# → 🌤️ weather(location=London) → sunny, 18°C
```

## Multi-tool Usage

```python
# Uses multiple tools automatically
await agent.run("Weather in Tokyo + calculate 15% tip on $45")
# → weather(location=Tokyo) + code(expression="45 * 0.15")

await agent.run("Read data.csv and create summary report")
# → csv(file=data.csv) + files(action=create)
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
await agent.run("Write a Python function to calculate Fibonacci numbers efficiently")

# Code analysis
await agent.run("Review this Python code and suggest improvements: [paste code here]")

# Debugging help
await agent.run("This code is throwing a KeyError. Help me debug it: [paste code]")
```

### Data Analyst
```python
agent = Agent("analyst")

# Data analysis
await agent.run("Analyze the sales data in quarterly_sales.csv and identify trends")

# Report generation
await agent.run("""
Load customer_data.csv, analyze customer segments, 
and create a summary report with key insights
""")
```

### Personal Assistant
```python
agent = Agent("assistant")

# Trip planning
await agent.run("""
Plan a 3-day trip to Tokyo with a budget of $2000. 
Consider weather, activities, and accommodation.
""")

# Schedule management
await agent.run("What's my schedule for today and what's the weather forecast?")
```

## Memory Examples

### Persistent Conversations
```python
agent = Agent("assistant")

# First conversation
await agent.run("Remember that I work at Google and I'm working on a React project")

# Later conversation (same or different session)
await agent.run("What project am I working on?")
# "You're working on a React project at Google"
```

### Custom Memory Backend
```python
from cogency.memory import Store

class DatabaseMemory(Store):
    def __init__(self, db_connection):
        self.db = db_connection
    
    async def save(self, content: str, metadata: dict = None):
        # Save to database
        pass
    
    async def search(self, query: str, limit: int = 5) -> list:
        # Search database
        return []

agent = Agent("assistant", memory=DatabaseMemory(db_connection))
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
    
    def get_schema(self) -> str:
        return "weather_api(city='string', country='US')"

agent = Agent("assistant", tools=[WeatherAPI()])
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

agent = Agent("assistant", tools=[DatabaseQuery(db_connection)])
```

## Configuration Examples

### Development Configuration
```python
agent = Agent(
    "dev-agent",
    debug=True,
    notify=True,
    mode="fast",
    depth=5
)
```

### Production Configuration
```python
from cogency import Robust, Observe

agent = Agent(
    "production-agent",
    robust=Robust(attempts=5, timeout=120.0),
    observe=Observe(metrics=True),
    persist=True,
    notify=False
)
```

### Specialized Agent
```python
agent = Agent(
    "researcher",
    mode="deep",
    depth=20,
    identity="You are a thorough researcher who cites sources."
)
```

## Error Handling Examples

### Basic Error Handling
```python
try:
    result = await agent.run("Complex query that might fail")
    print(result)
except Exception as e:
    print(f"Agent execution failed: {e}")
```

### Robust Configuration
```python
from cogency import Robust

# Automatic retry with backoff
agent = Agent(robust=Robust(
    attempts=3,
    timeout=30.0,
    backoff="exponential"
))

# This will automatically retry on failures
result = await agent.run("Query that might have transient failures")
```

### Custom Error Recovery
```python
async def safe_agent_run(agent, query, max_retries=3):
    for attempt in range(max_retries):
        try:
            return await agent.run(query)
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
    result = await agent.run(query)
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
            response = await agent.run(query)
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