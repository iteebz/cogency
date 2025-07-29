# Examples

Detailed code examples and walkthroughs for common Cogency use cases.

## Basic Examples

### Simple Query
```python
from cogency import Agent

agent = Agent("assistant")
result = await agent.run("What's 2 + 2?")
print(result)  # "4"
```

### Streaming Execution
```python
async for chunk in agent.stream("What's the weather in London?"):
    print(chunk, end="", flush=True)

# Output:
# 🌤️ weather(location='London') → sunny, 18°C
# The weather in London is currently sunny with a temperature of 18°C.
```

## Tool Usage Examples

### Calculator
```python
# Simple calculation
await agent.run("What's 15% of $1,250?")

# Complex expression
await agent.run("Calculate the compound interest: $1000 at 5% for 3 years")
```

### Web Search
```python
# Current information
await agent.run("What are the latest developments in quantum computing?")

# Specific search
await agent.run("Find Python tutorials for beginners")
```

### File Operations
```python
# Create a file
await agent.run("Create a file called todo.txt with my daily tasks")

# Read and analyze
await agent.run("Read the contents of data.csv and summarize the key findings")

# Edit existing file
await agent.run("Add a new task to todo.txt: 'Review documentation'")
```

### Multi-tool Queries
```python
# Weather + calculation
await agent.run("Weather in Tokyo and calculate flight cost: $450 + $120 tax")

# Search + file creation
await agent.run("Search for Python best practices and save the summary to notes.txt")
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
        await self.db.execute(
            "INSERT INTO memories (content, metadata) VALUES (?, ?)",
            (content, json.dumps(metadata))
        )
    
    async def search(self, query: str, limit: int = 5) -> list:
        results = await self.db.fetch(
            "SELECT content, metadata FROM memories WHERE content LIKE ? LIMIT ?",
            (f"%{query}%", limit)
        )
        return [{"content": r[0], "metadata": json.loads(r[1])} for r in results]

# Use custom memory
agent = Agent("assistant", memory=DatabaseMemory(db_connection))
```

## Custom Tool Examples

### API Integration Tool
```python
from cogency.tools import Tool, tool
import aiohttp

@tool
class WeatherAPI(Tool):
    def __init__(self):
        super().__init__("weather_api", "Get weather from custom API")
    
    async def run(self, city: str, country: str = "US") -> dict:
        async with aiohttp.ClientSession() as session:
            url = f"https://api.weather.com/v1/current?city={city}&country={country}"
            async with session.get(url) as response:
                data = await response.json()
                return {
                    "temperature": data["temp"],
                    "condition": data["condition"],
                    "humidity": data["humidity"],
                    "location": f"{city}, {country}"
                }
    
    def get_schema(self) -> str:
        return "weather_api(city='string', country='US')"

agent = Agent("assistant", tools=[WeatherAPI()])
await agent.run("Get weather for Paris, France using the weather API")
```

### Database Tool
```python
@tool
class DatabaseQuery(Tool):
    def __init__(self, db_connection):
        super().__init__("database", "Query the database")
        self.db = db_connection
    
    async def run(self, query: str, limit: int = 100) -> dict:
        try:
            results = await self.db.fetch(query, limit=limit)
            return {
                "results": results,
                "count": len(results),
                "success": True
            }
        except Exception as e:
            return {
                "error": str(e),
                "success": False
            }
    
    def get_schema(self) -> str:
        return "database(query='SQL string', limit=100)"

agent = Agent("assistant", tools=[DatabaseQuery(db_connection)])
await agent.run("Show me all users who signed up this month")
```

### File Processing Tool
```python
@tool
class ImageProcessor(Tool):
    def __init__(self):
        super().__init__("image_processor", "Process and analyze images")
    
    async def run(self, image_path: str, operation: str = "analyze") -> dict:
        if operation == "analyze":
            # Image analysis logic
            return {
                "dimensions": "1920x1080",
                "format": "JPEG",
                "size": "2.3MB",
                "colors": ["blue", "green", "white"]
            }
        elif operation == "resize":
            # Image resizing logic
            return {"message": f"Resized {image_path} successfully"}
    
    def get_schema(self) -> str:
        return "image_processor(image_path='string', operation='analyze|resize')"

agent = Agent("assistant", tools=[ImageProcessor()])
await agent.run("Analyze the image at photos/vacation.jpg")
```

## Configuration Examples

### Development Configuration
```python
# Fast iteration, detailed debugging
agent = Agent(
    "dev-agent",
    debug=True,          # Detailed tracing
    notify=True,         # Show progress
    mode="fast",         # Quick responses
    depth=5              # Limit iterations
)
```

### Production Configuration
```python
from cogency import Robust, Observe

# Production-ready with monitoring
agent = Agent(
    "production-agent",
    robust=Robust(
        attempts=5,
        timeout=120.0,
        rate_limit_rps=2.0
    ),
    observe=Observe(
        metrics=True,
        export_format="prometheus"
    ),
    persist=True,        # State persistence
    notify=False,        # Clean logs
    debug=False          # No debug overhead
)
```

### Specialized Agent
```python
# Research agent with deep thinking
agent = Agent(
    "researcher",
    mode="deep",         # Always use deep reasoning
    depth=20,            # Allow long reasoning chains
    identity="""You are a thorough researcher who:
    - Always cites sources
    - Provides comprehensive analysis
    - Considers multiple perspectives
    - Summarizes key findings clearly"""
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

@app.post("/stream")
async def stream_chat(query: str):
    async def generate():
        async for chunk in agent.stream(query):
            yield f"data: {chunk}\n\n"
    
    return StreamingResponse(generate(), media_type="text/plain")
```

### Discord Bot Integration
```python
import discord
from cogency import Agent

agent = Agent("discord-bot")

class CogencyBot(discord.Client):
    async def on_message(self, message):
        if message.author == self.user:
            return
        
        if message.content.startswith('!ask'):
            query = message.content[5:]  # Remove '!ask '
            response = await agent.run(query)
            await message.channel.send(response)

bot = CogencyBot()
bot.run('YOUR_BOT_TOKEN')
```

### Jupyter Notebook Integration
```python
# In a Jupyter notebook cell
from cogency import Agent
import asyncio

agent = Agent("notebook-assistant")

# Helper function for notebook use
def ask(query):
    return asyncio.run(agent.run(query))

# Usage
result = ask("Analyze this dataset and create visualizations")
print(result)
```

## Performance Examples

### Batch Processing
```python
import asyncio

agent = Agent("batch-processor")

async def process_batch(queries):
    tasks = [agent.run(query) for query in queries]
    results = await asyncio.gather(*tasks)
    return results

queries = [
    "Analyze sales data for Q1",
    "Generate marketing report",
    "Calculate customer metrics"
]

results = await process_batch(queries)
```

### Streaming with Progress
```python
async def stream_with_progress(agent, query):
    chunks = []
    async for chunk in agent.stream(query):
        chunks.append(chunk)
        print(f"\rProgress: {len(chunks)} chunks", end="", flush=True)
    
    print(f"\nComplete! Total chunks: {len(chunks)}")
    return "".join(chunks)

result = await stream_with_progress(agent, "Complex research query")
```

---

*These examples demonstrate the flexibility and power of Cogency for various use cases. Adapt them to your specific needs.*