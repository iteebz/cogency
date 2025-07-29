# Memory

Cogency agents have persistent memory that allows them to remember conversations and learn from interactions across sessions.

## How Memory Works

Agents automatically:
1. **Extract** important information from conversations
2. **Store** it with relevant metadata and tags
3. **Recall** relevant memories when needed for context

```python
# Agent automatically saves important information
await agent.run("Remember I work at Google and I'm building a React app")

# Later, agent recalls this information when relevant
await agent.run("What programming framework am I using?")
# "You're building a React app"
```

## Default Memory Backend

By default, agents use a filesystem-based memory backend:

```python
from cogency import Agent

# Uses .cogency/memory/ directory by default
agent = Agent("assistant")

# Custom memory directory
agent = Agent("assistant", memory_dir="./custom_memory")
```

Memory files are stored as JSON with content and metadata:
```json
{
  "content": "User works at Google and prefers Python",
  "metadata": {
    "timestamp": "2025-01-15T10:30:00Z",
    "tags": ["work", "preferences"],
    "user_id": "default"
  }
}
```

## Memory Operations

### Automatic Memory Extraction
The preprocessing phase automatically identifies and saves important information:

```python
await agent.run("I'm planning a trip to Japan next month and I'm vegetarian")
# Automatically saves: "User planning trip to Japan next month, vegetarian"
# Tags: ["travel", "dietary_preferences"]
```

### Memory Recall
The `recall` tool is automatically added when memory is enabled:

```python
await agent.run("What do you know about my dietary preferences?")
# Uses: recall(query="dietary preferences")
# Returns: "You're vegetarian"
```

### Manual Memory Operations
```python
# Force memory save
await agent.run("Remember this important fact: my birthday is March 15th")

# Search specific memories
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
        self.pool = None
    
    async def setup(self):
        self.pool = await asyncpg.create_pool(self.connection_string)
        
        # Create table if not exists
        async with self.pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS memories (
                    id SERIAL PRIMARY KEY,
                    content TEXT NOT NULL,
                    metadata JSONB,
                    created_at TIMESTAMP DEFAULT NOW(),
                    user_id TEXT DEFAULT 'default'
                )
            """)
    
    async def save(self, content: str, metadata: dict = None):
        metadata = metadata or {}
        async with self.pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO memories (content, metadata, user_id) VALUES ($1, $2, $3)",
                content, json.dumps(metadata), metadata.get('user_id', 'default')
            )
    
    async def search(self, query: str, limit: int = 5) -> list:
        async with self.pool.acquire() as conn:
            results = await conn.fetch("""
                SELECT content, metadata FROM memories 
                WHERE content ILIKE $1 
                ORDER BY created_at DESC 
                LIMIT $2
            """, f"%{query}%", limit)
            
            return [
                {
                    "content": row["content"],
                    "metadata": json.loads(row["metadata"])
                }
                for row in results
            ]
    
    async def clear(self):
        async with self.pool.acquire() as conn:
            await conn.execute("DELETE FROM memories")

# Usage
memory = PostgresMemory("postgresql://user:pass@localhost/db")
await memory.setup()
agent = Agent("assistant", memory=memory)
```

### Redis Memory Backend
```python
import redis.asyncio as redis
import json

class RedisMemory(Store):
    def __init__(self, redis_url="redis://localhost:6379"):
        self.redis_url = redis_url
        self.redis = None
    
    async def setup(self):
        self.redis = redis.from_url(self.redis_url)
    
    async def save(self, content: str, metadata: dict = None):
        metadata = metadata or {}
        memory_id = f"memory:{uuid.uuid4()}"
        
        memory_data = {
            "content": content,
            "metadata": metadata,
            "timestamp": time.time()
        }
        
        await self.redis.set(memory_id, json.dumps(memory_data))
        
        # Add to search index
        await self.redis.sadd("memory_index", memory_id)
    
    async def search(self, query: str, limit: int = 5) -> list:
        memory_ids = await self.redis.smembers("memory_index")
        results = []
        
        for memory_id in memory_ids:
            data = await self.redis.get(memory_id)
            if data:
                memory = json.loads(data)
                if query.lower() in memory["content"].lower():
                    results.append({
                        "content": memory["content"],
                        "metadata": memory["metadata"]
                    })
                    
                if len(results) >= limit:
                    break
        
        return results
    
    async def clear(self):
        memory_ids = await self.redis.smembers("memory_index")
        if memory_ids:
            await self.redis.delete(*memory_ids)
        await self.redis.delete("memory_index")

# Usage
memory = RedisMemory()
await memory.setup()
agent = Agent("assistant", memory=memory)
```

### Vector Memory Backend
```python
import chromadb
from sentence_transformers import SentenceTransformer

class VectorMemory(Store):
    def __init__(self, collection_name="cogency_memories"):
        self.client = chromadb.Client()
        self.collection = self.client.create_collection(collection_name)
        self.encoder = SentenceTransformer('all-MiniLM-L6-v2')
    
    async def save(self, content: str, metadata: dict = None):
        metadata = metadata or {}
        
        # Generate embedding
        embedding = self.encoder.encode([content])[0].tolist()
        
        # Store in ChromaDB
        self.collection.add(
            embeddings=[embedding],
            documents=[content],
            metadatas=[metadata],
            ids=[f"memory_{uuid.uuid4()}"]
        )
    
    async def search(self, query: str, limit: int = 5) -> list:
        # Generate query embedding
        query_embedding = self.encoder.encode([query])[0].tolist()
        
        # Search similar memories
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=limit
        )
        
        memories = []
        for i, doc in enumerate(results['documents'][0]):
            memories.append({
                "content": doc,
                "metadata": results['metadatas'][0][i],
                "similarity": 1 - results['distances'][0][i]  # Convert distance to similarity
            })
        
        return memories
    
    async def clear(self):
        self.client.delete_collection(self.collection.name)
        self.collection = self.client.create_collection(self.collection.name)

# Usage
agent = Agent("assistant", memory=VectorMemory())
```

## Memory Configuration

### Memory Tagging
```python
# Memories are automatically tagged based on content
await agent.run("I love hiking and outdoor activities")
# Tags: ["hobbies", "activities", "outdoor"]

await agent.run("I work as a software engineer at Microsoft")  
# Tags: ["work", "profession", "company"]
```

### User Isolation
```python
# Different users have separate memory spaces
agent1 = Agent("assistant")
await agent1.run("My name is Alice", user_id="user1")

agent2 = Agent("assistant") 
await agent2.run("My name is Bob", user_id="user2")

# Memories are isolated by user_id
await agent1.run("What's my name?", user_id="user1")  # "Alice"
await agent2.run("What's my name?", user_id="user2")  # "Bob"
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

## Memory Best Practices

### 1. Structured Information
```python
# Good: Structured, specific information
await agent.run("Remember: I work at Google as a Senior Software Engineer in the Cloud team, started in 2023")

# Less ideal: Vague information
await agent.run("Remember I work somewhere")
```

### 2. Explicit Memory Requests
```python
# Explicit memory save
await agent.run("Please remember this important detail: I'm allergic to peanuts")

# Implicit memory (agent decides what's important)
await agent.run("I had a great lunch today, but I'm allergic to peanuts so I had to be careful")
```

### 3. Memory Queries
```python
# Specific memory queries
await agent.run("What do you remember about my work?")
await agent.run("What are my dietary restrictions?")
await agent.run("What projects have I mentioned?")
```

### 4. Memory Management
```python
# Clear specific memories
await agent.run("Forget what I told you about my old job")

# Update memories
await agent.run("Update: I no longer work at Google, I now work at OpenAI")
```

## Memory Debugging

### View Memory Contents
```python
# Enable debug mode to see memory operations
agent = Agent("assistant", debug=True)

await agent.run("Remember I like Python")
# Debug output shows: "Memory saved: User prefers Python programming language"

await agent.run("What programming language do I like?")  
# Debug output shows: "Memory recalled: User prefers Python programming language"
```

### Memory Statistics
```python
# Custom memory backend with statistics
class StatisticsMemory(Store):
    def __init__(self):
        self.memories = []
        self.search_count = 0
        self.save_count = 0
    
    async def save(self, content: str, metadata: dict = None):
        self.save_count += 1
        self.memories.append({"content": content, "metadata": metadata})
    
    async def search(self, query: str, limit: int = 5) -> list:
        self.search_count += 1
        # Search logic...
        return results
    
    def get_stats(self):
        return {
            "total_memories": len(self.memories),
            "saves": self.save_count,
            "searches": self.search_count
        }

memory = StatisticsMemory()
agent = Agent("assistant", memory=memory)

# After some interactions
print(memory.get_stats())
# {"total_memories": 5, "saves": 5, "searches": 3}
```

## Memory Limitations

### Storage Limits
- **Filesystem**: Limited by disk space
- **Database**: Limited by database storage
- **Vector**: Limited by vector database capacity

### Search Performance
- **Simple search**: O(n) linear search through memories
- **Vector search**: O(log n) with proper indexing
- **Database search**: Depends on indexing strategy

### Memory Relevance
- Automatic relevance scoring helps surface the most relevant memories
- Older memories may become less relevant over time
- Consider implementing memory archiving for long-term storage

---

*Memory enables agents to build long-term relationships and provide personalized experiences across conversations.*