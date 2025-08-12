# Tools

Built-in tools auto-register and route intelligently. Create custom tools with zero ceremony.

## Built-in Tools

6 tools provide complete primitive coverage:

### 📁 **Files** - Filesystem I/O
```python
files(action='create', path='app.py', content='print("Hello World")')
files(action='read', path='config.json')
files(action='edit', path='app.py', line=1, content='print("Updated!")')
files(action='list', path='src')
```

### 💻 **Shell** - Command Execution
```python
shell(command='ls -la')
shell(command='python app.py')
shell(command='git status', working_dir='/path/to/repo')
```



### 📖 **Scrape** - Web Content Extraction
```python
scrape(url='https://example.com/article')  # Clean text
```

### 🔍 **Search** - Web Search
```python
search(query='latest AI developments 2024', max_results=5)
```

### 🧠 **Recall** - Agent Memory Search
```python
recall(query='user preferences', top_k=3, threshold=0.7)
```

### 📚 **Retrieve** - Document Search  
```python
retrieve(query='API documentation', top_k=5, threshold=0.7)
```

## Coverage

6 tools handle any agent task:
- **Local system**: Files + Shell
- **Web**: Scrape + Search  
- **Information**: Search + Scrape + Retrieve  
- **Memory**: Recall
- **Execution**: Shell
- **Persistence**: Files

## Composition Helpers

Explicit helpers for common combinations:

```python
from cogency import Agent, devops_tools, research_tools, web_tools

agent = Agent("devops", tools=devops_tools())        # Files + Shell + Search
agent = Agent("researcher", tools=research_tools())  # Search + Scrape + Retrieve
agent = Agent("web", tools=web_tools())              # Search + Scrape

from cogency import filesystem_tools, analysis_tools, memory_tools
agent = Agent("sysadmin", tools=filesystem_tools())  # Files + Shell
agent = Agent("analyst", tools=analysis_tools())     # Files + Retrieve + Recall
agent = Agent("librarian", tools=memory_tools())     # Retrieve + Recall
```

### Extensible

```python
agent = Agent("custom", tools=devops_tools() + [MyDatabaseTool()])  # Mix presets
agent = Agent("full", tools=research_tools() + filesystem_tools())  # Combine
```

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
        return {"result": f"Processed {query}"}

# Auto-registers
agent = Agent("assistant")
agent.run("Use my_tool with hello")
```

### Key Points
- **`@tool`** - Auto-registers
- **`args=dataclass`** - Auto-validates  
- **`schema`** - Explicit schema for LLM
- **`examples/rules`** - LLM guidance
- **Return `Result.ok(data)` or `Result.fail(error)`**

## Patterns

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