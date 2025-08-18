# Cogency

[![PyPI version](https://badge.fury.io/py/cogency.svg)](https://badge.fury.io/py/cogency)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

**Context-driven agents that work out of the box.**

```python
from cogency import Agent

agent = Agent()
result = await agent("Search for Python best practices and summarize")
```

**Zero ceremony. Maximum capability.**

- **🌐 Web-enabled** - Search and scrape with zero configuration
- **🔌 Multi-provider** - OpenAI, Anthropic, Gemini support
- **🛠️ Tool orchestration** - Files, shell, web tools auto-compose
- **🧠 Context injection** - Automatic assembly of relevant information
- **⚡️ Streaming** - Event-coordinated ReAct reasoning

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

Set your API key:
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

### Agent with Tools

```python
from cogency import Agent, BASIC_TOOLS
from cogency.tools import Search, Scrape

# Web-enabled agent
agent = Agent(tools=[Search(), Scrape()])
result = await agent("Search for Python best practices and summarize key points")

# All basic tools (Files, Shell)
agent = Agent(tools=BASIC_TOOLS)
result = await agent("Create a Python script that calculates factorial of 10")
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
- **Working**: Tool execution history

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

### Streaming

```python
from cogency import Agent

agent = Agent()
async for event in agent.stream("Complex research task requiring multiple steps"):
    if event["type"] == "reasoning":
        print(f"Thinking: {event['content'][:100]}...")
    elif event["type"] == "complete":
        print(f"Final: {event['answer']}")
```

### Agent with Multiple Providers

```python
from cogency import Agent
from cogency.lib.providers import Anthropic, Nomic

# Provider agnostic: Mix any LLM with any Embedder
agent = Agent(llm=Anthropic(), embedder=Nomic())
result = await agent("Compare Python and Rust for systems programming")
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

**That's it.** No configuration, no setup, just working agents.

*v2.1.0: Web capabilities, multi-provider support, Result types - zero ceremony preserved.*