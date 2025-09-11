# Cogency

**Streaming agents**

Resume execution after tool calls. No context replay. Linear token scaling.

```python
from cogency import Agent

agent = Agent()
async for event in agent("Debug this Python script and fix any issues"):
    if event["type"] == "respond":
        print(event["content"])
```

## Resume vs Replay

**Traditional frameworks:** Context replay grows quadratically
```
Turn 1: [Messages 1-10] → Tool → [Messages 1-11] → Tool
Turn 2: [Messages 1-11] → Tool → [Messages 1-12] → Tool  
# Token cost: O(n²) growth
```

**Cogency:** Stream resumes after tool execution
```
§THINK: Let me examine the code structure first
§CALLS: [{"name": "read", "args": {"file": "main.py"}}]
§EXECUTE:
[SYSTEM: Found syntax error on line 15]
§RESPOND: Fixed the missing semicolon. Code runs correctly now.
```

**Context stays constant. Token usage stays flat.**

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
agent = Agent(mode="resume")     # Persistent session, O(n) scaling

# Replay: HTTP requests  
agent = Agent(mode="replay")     # Universal compatibility, O(n²) scaling

# Auto: Resume with HTTP fallback
agent = Agent(mode="auto")       # Production recommended
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
agent = Agent()
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

# Custom tools
from cogency import Tool
from cogency.core.result import Ok

class DatabaseTool(Tool):
    name = "query_db"
    description = "Execute SQL queries"
    
    async def execute(self, sql: str, user_id: str):
        # Your implementation
        return Ok("Query results...")

agent = Agent(tools=[DatabaseTool()])
```

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