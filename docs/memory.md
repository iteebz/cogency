# Memory

Cogency agents have persistent memory that remembers conversations across sessions.

## How Memory Works

Agents automatically:
1. **Extract** important information from conversations
2. **Store** it with relevant metadata and tags
3. **Recall** relevant memories when needed

```python
# Agent automatically saves important information
await agent.run("Remember I work at Google and I'm building a React app")

# Later, agent recalls this information when relevant
await agent.run("What programming framework am I using?")
# "You're building a React app"
```

## Default Memory Backend

```python
from cogency import Agent

# Uses .cogency/memory/ directory by default
agent = Agent("assistant")

# Custom memory backend
from cogency.memory import Chroma
agent = Agent("assistant", memory=Chroma())
```

## Memory Operations

### Automatic Memory Extraction
```python
await agent.run("I'm planning a trip to Japan next month and I'm vegetarian")
# Automatically saves: "User planning trip to Japan next month, vegetarian"
```

### Memory Recall
```python
await agent.run("What do you know about my dietary preferences?")
# Uses recall tool to search memory
# Returns: "You're vegetarian"
```

### Manual Memory Operations
```python
# Force memory save
await agent.run("Remember this: my birthday is March 15th")

# Search memories
await agent.run("What have I told you about my work?")
```

## Custom Memory Backends

### Database Memory Backend
```python
from cogency.memory import Store
import asyncpg

class PostgresMemory(Store):
    def __init__(self, connection_string):
        self.connection_string = connection_string
    
    async def save(self, content: str, metadata: dict = None):
        # Save to PostgreSQL
        pass
    
    async def search(self, query: str, limit: int = 5) -> list:
        # Search PostgreSQL
        return []

memory = PostgresMemory("postgresql://user:pass@localhost/db")
agent = Agent("assistant", memory=memory)
```

### Vector Memory Backend
```python
import chromadb

class VectorMemory(Store):
    def __init__(self):
        self.client = chromadb.Client()
        self.collection = self.client.create_collection("memories")
    
    async def save(self, content: str, metadata: dict = None):
        # Save with embedding
        pass
    
    async def search(self, query: str, limit: int = 5) -> list:
        # Semantic search
        return []

agent = Agent("assistant", memory=VectorMemory())
```

## Memory Configuration

### User Isolation
```python
# Different users have separate memory spaces
agent = Agent("assistant")
await agent.run("My name is Alice", user_id="user1")
await agent.run("My name is Bob", user_id="user2")

# Memories are isolated by user_id
await agent.run("What's my name?", user_id="user1")  # "Alice"
```

### Memory Persistence
```python
# Memory persists across agent instances
agent1 = Agent("assistant")
await agent1.run("Remember I prefer dark mode")

# Later, with a new agent instance
agent2 = Agent("assistant")  # Same memory backend
await agent2.run("What are my UI preferences?")  # "You prefer dark mode"
```

## Best Practices

### Structured Information
```python
# Good: Structured, specific information
await agent.run("Remember: I work at Google as a Senior Software Engineer")

# Less ideal: Vague information
await agent.run("Remember I work somewhere")
```

### Memory Debugging
```python
# Enable debug mode to see memory operations
agent = Agent("assistant", debug=True)

await agent.run("Remember I like Python")
# Debug output shows memory operations
```

---

*Memory enables agents to build long-term relationships across conversations.*