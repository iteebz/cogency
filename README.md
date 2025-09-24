# Cogency

**Streaming agents that resume execution after tool calls**

Break free from quadratic context replay. **Linear token scaling** enables conversations of unlimited depth.

## Performance Breakthrough

**Traditional frameworks replay entire context every tool call:**
```
Turn 8: 31,200 tokens (5.2x cost)
Turn 16: 100,800 tokens (9.3x cost) 
Turn 32: 355,200 tokens (17.4x cost)
```

**Cogency maintains streaming state:**
```
Turn 8: 6,000 tokens
Turn 16: 10,800 tokens  
Turn 32: 20,400 tokens
```

**Result: 94% token reduction at 32 turns.** The deeper the conversation, the greater the savings.

## Core Innovation

**Stream injection with delimiter protocol:**

```python
from cogency import Agent

agent = Agent(llm="openai")
async for event in agent("Debug this Python script and fix any issues"):
    if event["type"] == "respond":
        print(event["content"])
```

**Agent signals execution state explicitly:**
```
§think: I need to examine the code structure first
§call: {"name": "file_read", "args": {"file": "main.py"}}  
§execute
[SYSTEM: Found syntax error on line 15]
§respond: Fixed the missing semicolon. Code runs correctly now.
§end
```

**Stream pauses for tool execution, then resumes with results injected.** No context replay needed.

## Key Features

**🚀 Stream Resumption**: WebSocket sessions maintain context across tool calls  
**💾 Dual Memory**: Passive profiles + active recall across conversations  
**🔒 Layered Security**: Semantic reasoning + execution-level validation  
**🔌 Multi-Provider**: OpenAI Realtime, Gemini Live, Claude HTTP  
**⚡ Real-time Streaming**: Word-level or semantic-level event control  
**🔍 9 Built-in Tools**: Complete file_, web_, memory_, and system_ operations

## Installation

```bash
pip install cogency
export OPENAI_API_KEY="your-key"
```

Verify installation:
```bash
python -c "from cogency import Agent; print('✓ Cogency installed')"
```

## Execution Modes

```python
# Resume: WebSocket streaming (default)
agent = Agent(llm="openai", mode="resume")     # Persistent session, O(n) scaling

# Replay: HTTP requests  
agent = Agent(llm="openai", mode="replay")     # Universal compatibility, O(n²) scaling

# Auto: Resume with HTTP fallback
agent = Agent(llm="openai", mode="auto")       # Production recommended
```

## Multi-Provider

```python
agent = Agent(llm="openai")     # GPT-4o Realtime API
agent = Agent(llm="gemini")     # Gemini Live WebSocket  
agent = Agent(llm="anthropic")  # Claude HTTP
```

## Usage

```python
from cogency import Agent

# Basic usage
agent = Agent(llm="openai")
async for event in agent("What files are in this directory?"):
    if event["type"] == "respond":
        print(event["content"])

# Multi-turn conversations
async for event in agent(
    "Continue our code review",
    user_id="developer", 
    conversation_id="review_session"
):
    if event["type"] == "respond":
        print(event["content"])

# 9 built-in tools:
# file_read, file_write, file_edit, file_list, file_search
# web_search, web_scrape, recall, shell

# Custom tools
from cogency import Tool, ToolResult

class DatabaseTool(Tool):
    name = "query_db"
    description = "Execute SQL queries"
    
    async def execute(self, sql: str, user_id: str):
        # Your implementation
        return ToolResult(outcome="Query executed successfully", content="Query results...")

agent = Agent(llm="openai", tools=[DatabaseTool()])
```

## Streaming Control

**chunks=False (default):** Complete semantic units
```python
async for event in agent("Debug this code", chunks=False):
    if event["type"] == "think":
        print(f"🤔 {event['content']}")  # "I need to analyze this code structure"
    elif event["type"] == "respond":
        print(f"💬 {event['content']}")  # "The syntax error is on line 15"
```

**chunks=True:** Real-time event streaming
```python  
async for event in agent("Debug this code", chunks=True):
    if event["type"] == "think":
        print(event["content"], end="")  # "I need" " to" " analyze"...
    elif event["type"] == "respond":  
        print(event["content"], end="")  # "The" " syntax" " error"...
```

See [ARCHITECTURE.md](docs/ARCHITECTURE.md) for detailed streaming behavior and frontend integration patterns.

## Performance

Token efficiency scales exponentially with conversation depth:

| Turns | Traditional O(n²) | Streaming O(n) | Efficiency |
|-------|------------------|----------------|------------|
| 1     | 1,800           | 1,800          | 1.0x       |
| 2     | 4,200           | 2,400          | 1.8x       |
| 4     | 10,800          | 3,600          | 3.0x       |
| 8     | 31,200          | 6,000          | **5.2x**   |
| 16    | 100,800         | 10,800         | **9.3x**   |
| 32    | 355,200         | 20,400         | **17.4x**  |

**Longer agents = exponentially better efficiency**

Mathematical proof: [docs/proof.md](docs/proof.md)

## License

Apache 2.0
