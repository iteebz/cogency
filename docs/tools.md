# Tools

Built-in tools auto-register and route intelligently. Create custom tools with zero ceremony.

## Canonical 5 Tools

Cogency ships with 5 core tools that provide complete primitive coverage:

### 📁 **Files** - Local Filesystem I/O
```python
files(action='create', path='app.py', content='print("Hello World")')
files(action='read', path='config.json')
files(action='edit', path='app.py', line=1, content='print("Updated!")')
files(action='list', path='src')
```

### 💻 **Shell** - System Command Execution
```python
shell(command='ls -la')
shell(command='python app.py')
shell(command='git status', working_dir='/path/to/repo')
```

### 🌐 **HTTP** - Universal Network Primitive
```python
http(url='https://api.github.com/user', method='get', headers={'Authorization': 'token xyz'})
http(url='https://api.service.com/data', method='post', json_data={'name': 'test'})
```

### 📖 **Scrape** - Intelligent Web Content Extraction
```python
scrape(url='https://example.com/article')  # Returns clean text content
```

### 🔍 **Search** - Web Information Discovery
```python
search(query='latest AI developments 2024', max_results=5)
```

## Tool Coverage

These 5 tools compose to handle any reasonable AI agent task:
- **Local system**: Files + Shell
- **Network/Web**: HTTP + Scrape + Search  
- **Information gathering**: Search + Scrape
- **Execution**: Shell
- **Data persistence**: Files

**HTTP as the universal fallback**: When specialized tools fail or don't exist, HTTP can call any API, webhook, or service.

## Custom Tools

```python
from cogency.tools import Tool, tool
from dataclasses import dataclass

@dataclass 
class MyToolArgs:
    query: str
    limit: int = 10

@tool  # Auto-registers
class MyTool(Tool):
    def __init__(self):
        super().__init__(
            name="my_tool",
            description="Does something useful", 
            schema="my_tool(query: str, limit: int = 10)",
            emoji="🔧",
            params=MyToolArgs,  # Auto-validation
            examples=["my_tool(query='hello', limit=5)"],
            rules=["Keep queries concise"]
        )
    
    async def run(self, query: str, limit: int = 10) -> dict:
        # Your logic here
        return {"result": f"Processed {query}"}

# Tool auto-registers - zero ceremony
agent = Agent("assistant")
await agent.run("Use my_tool with hello")
```

### Key Points
- **`@tool`** - Auto-registers with agent
- **`params=dataclass`** - Auto-validates parameters  
- **`schema`** - Explicit schema string for LLM
- **`examples/rules`** - LLM guidance
- **Return `Result.ok(data)` or `Result.fail(error)`**

## Extension Patterns

```python
# Memory-aware tool
@tool
class MemoryTool(Tool):
    def __init__(self, memory=None):
        super().__init__("memory_tool", "Searches memory")
        self.memory = memory

# API integration
@tool  
class APITool(Tool):
    def __init__(self):
        super().__init__("api", "External API calls")
        self.client = HttpClient()
        
    async def run(self, endpoint: str) -> dict:
        response = await self.client.get(endpoint)
        return {"data": response.json()}
```