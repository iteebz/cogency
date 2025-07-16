# memory

Agent memory system with clean primitives and pluggable backends.

## design principles

- **primitive-first**: minimal, composable abstractions
- **agent-controlled**: memory operations are tools, not automatic
- **backend-agnostic**: filesystem, vector db, whatever
- **async-native**: parallel operations during reasoning loops

## memory types

### message
Fine-grained message recall
- exact matching for user preferences
- tags: `["message", "user-pref"]`

### summary
Thread/session summaries  
- context rehydration, token efficiency
- tags: `["summary", "session:current"]`

### fact
Semantic knowledge units
- embedding-based similarity search
- tags: `["fact", "domain:streaming"]`

### context
Recent interaction history
- chronological working memory
- tags: `["context", "recent"]`

## usage

### basic api

```python
from cogency import FSMemory

memory = FSMemory(memory_dir=".memory")

# store
await memory.memorize("User prefers dark mode", tags=["pref"])

# retrieve  
results = await memory.recall("user preferences")
```

### with agents

```python
from cogency import Agent, FSMemory
from cogency.tools.memory import MemorizeTool, RecallTool

memory = FSMemory()
memory_tools = [MemorizeTool(memory), RecallTool(memory)]
agent = Agent("assistant", tools=memory_tools)

# agent can now remember things
await agent.run("Remember I work at OpenAI")
await agent.run("What do you know about my work?")
```

## backends

### fsmemory
filesystem storage with json

### semanticmemory  
embedding-based similarity search

```python
from cogency.memory import SemanticMemory
from cogency.embed import NomicEmbed

memory = SemanticMemory(embed_provider=NomicEmbed())
```

## extending

implement `BaseMemory` for custom backends:

```python
class CustomMemory(BaseMemory):
    async def memorize(self, content: str, **kwargs):
        pass
        
    async def recall(self, query: str, **kwargs):
        pass
```