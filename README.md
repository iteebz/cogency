# Cogency

**Stateful streams, stateless agents.**

**Performance:** O(n²) → O(n) scaling. Token efficiency grows with conversation depth.

```python
from cogency import Agent

agent = Agent()
result = await agent("Debug this Python script and fix any issues")
```

## Agent Stream Continuity

```python
# Traditional: Context replay grows quadratically (O(n²))
# 8-step task: ~31,200 tokens

# Cogency: Constant incremental cost (O(n))
# 8-step task: ~6,000 tokens (81% reduction)
```

Agents pause stream, execute tools, resume same session:

```python
§THINK: Let me examine the code structure first
§CALLS: [{"name": "file_read", "args": {"path": "main.py"}}]
§YIELD:
[SYSTEM: Found syntax error on line 15]  
§RESPOND: Fixed the missing semicolon. Code should run correctly now.
```

**Context stays constant. Token usage stays flat.**

## Stateless Orchestration

**Agent orchestration:** Pure functions  
**State boundaries:** Context assembly wraps storage

```python
agent = Agent()  # Configuration closure
result = await agent(query)  # Stateless execution
```

## Multi-Provider Architecture

```python
agent = Agent(llm="openai")     # GPT-4o Realtime API
agent = Agent(llm="gemini")     # Gemini Live WebSocket  
agent = Agent(llm="anthropic")  # Claude HTTP fallback
```

**Execution Modes:**
- **Resume:** Single WebSocket session, context injection
- **Replay:** HTTP requests, context rebuilding  
- **Auto:** WebSocket with HTTP fallback

**Execution Characteristics:**
- WebSocket: Sub-second tool injection, persistent sessions
- HTTP: Universal compatibility, automatic fallback
- Scaling: Linear token growth vs quadratic in traditional frameworks

## Installation

```bash
pip install cogency
export OPENAI_API_KEY="your-key"
```

## Usage

```python
from cogency import Agent

# Basic usage
agent = Agent()
result = await agent("What files are in this directory?")

# Multi-turn conversations
result = await agent(
    "Continue our code review",
    user_id="developer", 
    conversation_id="review_session"
)

# Custom tools
from cogency import Tool

class DatabaseTool(Tool):
    name = "query_db"
    description = "Execute SQL queries"
    
    async def execute(self, sql: str, user_id: str):
        return Ok("Query results...")

agent = Agent(tools=[DatabaseTool()])
```

## License

Apache 2.0