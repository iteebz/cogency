# Tools

Cogency comes with a comprehensive suite of built-in tools and supports easy custom tool creation.

## Built-in Tools

Agents automatically discover and use these tools based on query context:

### 🧮 Calculator
Mathematical expressions and calculations.
```python
await agent.run("What's 15% of $1,250?")
# Uses: calculator(expression="1250 * 0.15")
```

### 🔍 Search  
Web search using DuckDuckGo for current information.
```python
await agent.run("Latest news about quantum computing")
# Uses: search(query="quantum computing news 2025")
```

### 🌤️ Weather
Current weather conditions and forecasts.
```python
await agent.run("What's the weather in Tokyo?")
# Uses: weather(location="Tokyo")
```

### 📁 Files
File operations - create, read, edit, list, delete files.
```python
await agent.run("Create a file called notes.txt with my meeting notes")
# Uses: files(action="create", filename="notes.txt", content="...")
```

### 💻 Shell
Execute system commands safely.
```python
await agent.run("List all Python files in the current directory")
# Uses: shell(command="find . -name '*.py'")
```

### 🐍 Code
Python code execution in a sandboxed environment.
```python
await agent.run("Generate a list of prime numbers up to 100")
# Uses: code(script="def is_prime(n): ...")
```

### 📊 CSV
Data processing and analysis of CSV files.
```python
await agent.run("Analyze the sales data in data.csv")
# Uses: csv(file="data.csv", operation="analyze")
```

### 🗄️ SQL
Database querying and management.
```python
await agent.run("Show me all users from the database")
# Uses: sql(query="SELECT * FROM users")
```

### 🌐 HTTP
Make HTTP requests with automatic JSON parsing.
```python
await agent.run("Get the current Bitcoin price from the API")
# Uses: http(url="https://api.coinbase.com/v2/exchange-rates", method="GET")
```

### 🕒 Time
Date and time operations, timezone conversions.
```python
await agent.run("What time is it in Tokyo right now?")
# Uses: time(operation="current", timezone="Asia/Tokyo")
```

### 📅 Date
Date calculations and formatting.
```python
await agent.run("What date will it be 30 days from now?")
# Uses: date(operation="add", days=30)
```

### 🔗 Scrape
Web scraping with content extraction.
```python
await agent.run("Scrape the main content from this webpage")
# Uses: scrape(url="https://example.com")
```

### 🧠 Recall
Memory search and retrieval (automatically added when memory is enabled).
```python
await agent.run("What did I tell you about my preferences?")
# Uses: recall(query="user preferences")
```

## Tool Selection

The preprocessing phase intelligently selects 3-5 relevant tools from the full registry:

```python
# Query: "Weather in Tokyo and calculate flight cost $450 + tax $67"
# Selected tools: weather, calculator (2 out of 13 available)

# Query: "Analyze data.csv and create a summary report"  
# Selected tools: csv, files (2 out of 13 available)
```

This keeps the system performant while maintaining full capability.

## Creating Custom Tools

### Basic Custom Tool

```python
from cogency.tools import Tool, tool

@tool
class MyTool(Tool):
    def __init__(self):
        super().__init__(
            name="my_tool",
            description="Does something useful",
            emoji="🔧"  # Optional
        )
    
    async def run(self, param: str) -> dict:
        # Your tool logic here
        result = f"Processed: {param}"
        return {"result": result}
    
    def get_schema(self) -> str:
        return "my_tool(param='string')"
    
    def get_usage_examples(self) -> list:
        return ["my_tool(param='hello world')"]

# Tool auto-registers - just create your agent
agent = Agent("assistant")
await agent.run("Use my_tool with hello")
```

### Tool with Parameters

```python
@tool
class DatabaseTool(Tool):
    def __init__(self):
        super().__init__("database", "Query database tables")
    
    async def run(self, table: str, limit: int = 10) -> dict:
        # Database query logic
        results = query_database(table, limit)
        return {"results": results, "count": len(results)}
    
    def get_schema(self) -> str:
        return "database(table='string', limit=10)"
```

### Tool with Memory Access

```python
@tool  
class MemoryTool(Tool):
    def __init__(self, memory=None):
        super().__init__("memory_tool", "Uses agent memory")
        self.memory = memory
    
    async def run(self, query: str) -> dict:
        if self.memory:
            results = await self.memory.search(query)
            return {"memories": results}
        return {"error": "No memory available"}
```

### Tool with Error Handling

```python
@tool
class APITool(Tool):
    def __init__(self):
        super().__init__("api_tool", "Calls external API")
    
    async def run(self, endpoint: str) -> dict:
        try:
            response = await make_api_call(endpoint)
            return {"data": response, "success": True}
        except Exception as e:
            # Errors are automatically caught and formatted
            return {"error": str(e), "success": False}
```

## Using Custom Tools

### Explicit Tool List
```python
from cogency import Agent

# Specify tools explicitly
agent = Agent("assistant", tools=[MyTool(), DatabaseTool()])
```

### Mixed Built-in and Custom
```python
from cogency.tools import Calculator, Search

# Mix built-in and custom tools
agent = Agent("assistant", tools=[
    Calculator(),
    Search(), 
    MyTool(),
    DatabaseTool()
])
```

### Auto-Registration
```python
# Tools with @tool decorator auto-register
@tool
class AutoTool(Tool):
    # ... implementation

# Just create agent - tool is automatically available
agent = Agent("assistant")
```

## Tool Development Best Practices

### 1. Clear Descriptions
```python
super().__init__(
    name="weather",
    description="Get current weather conditions and forecasts for any location worldwide"
)
```

### 2. Comprehensive Schema
```python
def get_schema(self) -> str:
    return "weather(location='string', units='metric|imperial', forecast_days=1)"
```

### 3. Realistic Examples
```python
def get_usage_examples(self) -> list:
    return [
        "weather(location='London')",
        "weather(location='New York', units='imperial')",
        "weather(location='Tokyo', forecast_days=3)"
    ]
```

### 4. Structured Returns
```python
async def run(self, location: str) -> dict:
    weather_data = get_weather(location)
    return {
        "location": location,
        "temperature": weather_data.temp,
        "condition": weather_data.condition,
        "humidity": weather_data.humidity,
        "success": True
    }
```

### 5. Graceful Error Handling
```python
async def run(self, location: str) -> dict:
    try:
        return await get_weather_data(location)
    except LocationNotFound:
        return {"error": f"Location '{location}' not found", "success": False}
    except APIError as e:
        return {"error": f"Weather service unavailable: {e}", "success": False}
```

## Tool Registry

The tool registry automatically manages tool discovery and selection:

```python
from cogency.tools import get_tools

# Get all available tools
all_tools = get_tools()
print(f"Available tools: {[tool.name for tool in all_tools]}")

# Tools are automatically filtered based on query context
```

## Advanced Tool Features

### Conditional Tool Loading
```python
@tool
class DatabaseTool(Tool):
    def __init__(self):
        if not database_available():
            raise ToolUnavailable("Database not configured")
        super().__init__("database", "Query database")
```

### Tool Dependencies
```python
@tool
class AnalyticsTool(Tool):
    def __init__(self):
        super().__init__("analytics", "Data analysis")
        self.requires = ["csv", "calculator"]  # Suggest other tools
```

### Async Tool Initialization
```python
@tool
class AsyncTool(Tool):
    def __init__(self):
        super().__init__("async_tool", "Async operations")
    
    async def setup(self):
        # Async initialization if needed
        self.client = await create_async_client()
```

---

*See [Examples](examples.md) for complete tool usage examples.*