# Cogency: Stateless Context-Driven Agent Framework

Context injection + LLM inference = complete reasoning engine.

After extensive research (340 commits), we discovered agents work better as functions.

## Quick Start

```python
import asyncio
from cogency import Agent

async def main():
    agent = Agent()
    response = await agent("What are the benefits of async/await in Python?")
    print(response)

# Run with: python -m asyncio your_script.py
asyncio.run(main())
```

## Installation

```bash
pip install cogency
```

Set your OpenAI API key:
```bash
export OPENAI_API_KEY="your-api-key-here"
```

## Examples

### Basic Agent

```python
from cogency import Agent

agent = Agent()
response = await agent("Explain quantum computing in simple terms")
```

### ReAct Agent with Tools

```python
from cogency import ReAct

agent = ReAct(verbose=True)
result = await agent.solve("Create a Python script that calculates factorial of 10")
print(result["final_answer"])
```

### User-Specific Context

```python
from cogency import Agent, profile

# Set user preferences (optional)
profile("alice", 
        name="Alice Johnson",
        preferences=["Python", "Machine Learning"],
        context="Senior data scientist working on NLP projects")

agent = Agent()
response = await agent("Recommend a good ML library for text processing", user_id="alice")
```

### Custom Knowledge Base

```python
from cogency.storage import add_document

# Add documents to knowledge base (optional)
add_document("python_guide", "Python is a high-level programming language...")
add_document("ml_basics", "Machine learning is a subset of artificial intelligence...")

# Agent automatically searches relevant documents for context
agent = Agent()
response = await agent("What's the difference between Python and machine learning?")
```

## Architecture

Context-driven agents work by injecting relevant information before each query:

```python
async def agent_call(query: str, user_id: str = "default") -> str:
    ctx = context(query, user_id)  # Assembles relevant context
    prompt = f"{ctx}\n\nQuery: {query}"
    return await llm.generate(prompt)
```

Context sources include:
- **System**: Base instructions
- **Conversation**: Recent message history  
- **Knowledge**: Semantic search results
- **Memory**: User profile and preferences
- **Working**: Tool execution history (for ReAct agents)

## Design Principles

- **Zero writes** during reasoning - no database operations in the hot path
- **Pure functions** for context assembly - deterministic and testable
- **Read-only** context sources - graceful degradation on failures
- **Optional persistence** - conversation history saved asynchronously

## API Reference

### Agent

Simple conversational agent with context injection.

```python
agent = Agent()
response = await agent(query: str, user_id: str = "default") -> str
```

### ReAct  

Tool-using agent with Reason + Act loops.

```python
agent = ReAct(tools=None, user_id="default", verbose=False)
result = await agent.solve(task: str, max_iterations: int = 5) -> dict
```

### Context Functions

```python
from cogency import profile
from cogency.storage import add_document

# User profiles
profile(user_id, name=None, preferences=None, context=None)

# Knowledge base
add_document(doc_id: str, content: str, metadata: dict = None)
```

## Testing

```bash
# Install dev dependencies
poetry install

# Run tests
pytest tests/
```

## Documentation

See `docs/blueprint.md` for complete technical specification.

*v2.0.0 represents a complete architectural rewrite based on empirical evidence that simpler approaches work better for LLM-based reasoning systems.*