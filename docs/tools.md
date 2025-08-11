# Tools

Built-in tools auto-register and route intelligently. Create custom tools with zero ceremony.

## Core Tools

Cogency ships with 6 built-in tools that provide complete primitive coverage:

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



### 📖 **Scrape** - Intelligent Web Content Extraction
```python
scrape(url='https://example.com/article')  # Returns clean text content
```

### 🔍 **Search** - Web Information Discovery
```python
search(query='latest AI developments 2024', max_results=5)
```

### 🧠 **Recall** - Archival Memory Retrieval
```python
recall(query='user preferences', layer='topics', limit=3)
```

### 📚 **Retrieval** - Document Semantic Search
```python
retrieval(query='API documentation', top_k=5, threshold=0.7)
```

## Tool Coverage

These 6 tools compose to handle any reasonable AI agent task:
- **Local system**: Files + Shell
- **Network/Web**: Scrape + Search  
- **Information gathering**: Search + Scrape + Retrieval
- **Memory systems**: Recall + Retrieval
- **Execution**: Shell
- **Data persistence**: Files

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
            args=MyToolArgs,  # Auto-validation
            examples=["my_tool(query='hello', limit=5)"],
            rules=["Keep queries concise"]
        )
    
    async def run(self, query: str, limit: int = 10) -> dict:
        # Your logic here
        return {"result": f"Processed {query}"}

# Tool auto-registers - zero ceremony
agent = Agent("assistant")
agent.run("Use my_tool with hello")
```

### Key Points
- **`@tool`** - Auto-registers with agent
- **`args=dataclass`** - Auto-validates arguments  
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