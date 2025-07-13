# Memory Architecture

Cogency's memory system provides clean, extensible primitives for agent memory operations. Built from first principles for async-first agent architectures.

## Core Design Philosophy

- **Primitive-first**: Core abstractions stay minimal and composable
- **Agent-controlled**: Memory operations are tools agents invoke, not automatic behaviors
- **Backend-agnostic**: Clean separation between memory interface and storage implementation
- **Async-native**: Parallel memory operations during ReAct reasoning loops

## Memory Types

Cogency supports four fundamental memory modalities:

### 1. Message-Level Recall
Fine-grained retrieval of specific messages or interactions.
- High precision, exact matching
- User preferences, specific phrasing
- Tags: `["message", "user-pref"]`

### 2. Message Block / Thread Summary Recall  
Medium granularity summaries of conversations or task runs.
- Context rehydration, token efficiency
- Session continuity across interruptions
- Tags: `["summary", "session:jul13"]`

### 3. Fact Statement Semantic Recall
Abstracted knowledge units for reasoning.
- Semantic similarity search via embeddings
- "X implies Y" or "A happened at T" statements
- Tags: `["fact", "domain:streaming"]`

### 4. Sliding Context History
Volatile working memory for recent interactions.
- Chronological buffer, short-term continuity
- Not persistent unless explicitly memorized
- Tags: `["context", "recent"]`

## Core Interface

### BaseMemory

```python
from cogency.memory import BaseMemory, MemoryArtifact, MemoryType

class BaseMemory(ABC):
    @abstractmethod
    async def memorize(
        self, 
        content: str,
        memory_type: MemoryType = MemoryType.FACT,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> MemoryArtifact:
        """Store content in memory."""
        
    @abstractmethod
    async def recall(
        self, 
        query: str,
        limit: Optional[int] = None,
        tags: Optional[List[str]] = None,
        memory_type: Optional[MemoryType] = None,
        since: Optional[str] = None,  # ISO datetime
        **kwargs
    ) -> List[MemoryArtifact]:
        """Retrieve relevant content."""
```

### MemoryArtifact

```python
@dataclass
class MemoryArtifact:
    content: str
    memory_type: MemoryType = MemoryType.FACT
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
```

### MemoryType

```python
class MemoryType(Enum):
    MESSAGE = "message"    # Fine-grained message recall
    SUMMARY = "summary"    # Thread/block summaries
    FACT = "fact"         # Semantic knowledge units  
    CONTEXT = "context"   # Working memory/history
```

## Implementations

### FSMemory
Simple filesystem backend with JSON storage.
```python
from cogency.memory import FSMemory

memory = FSMemory(memory_dir=".cogency_memory")
```

### SemanticMemory  
Embedding-based semantic search with text fallback.
```python
from cogency.memory import SemanticMemory
from cogency.embed import NomicEmbed

embed_provider = NomicEmbed()
memory = SemanticMemory(
    embed_provider=embed_provider,
    similarity_threshold=0.7
)
```

## Agent Integration

Memory operations are available as tools:

```python
from cogency.memory.tools import MemorizeTool, RecallTool

# In agent setup
memorize_tool = MemorizeTool(memory)
recall_tool = RecallTool(memory)

# Agent can use in parallel
tasks = [
    agent.memorize("Important insight about streaming patterns"),
    agent.recall("previous streaming insights")
]
results = await asyncio.gather(*tasks)
```

## Common Patterns

### Type-Scoped Queries
```python
# Recall only facts about a topic
facts = await memory.recall(
    "streaming patterns",
    memory_type=MemoryType.FACT
)

# Get recent message history
recent = await memory.recall(
    "",
    memory_type=MemoryType.CONTEXT,
    since="2025-07-13T10:00:00"
)
```

### Tag-Based Organization
```python
# Store with structured tagging
await memory.memorize(
    "Streaming agents need buffering for parallel operations",
    memory_type=MemoryType.FACT,
    tags=["streaming", "architecture", "performance"],
    metadata={"priority": "high", "domain": "cogency"}
)

# Retrieve by domain
insights = await memory.recall(
    "performance optimization",
    tags=["architecture"]
)
```

### Time-Based Filtering
```python
# Session-specific recall
session_memories = await memory.recall(
    "user preferences",
    since="2025-07-13T00:00:00",
    tags=["session:current"]
)
```

## Utility Methods

For convenience (optional):

```python
# Get memories by type only
facts = await memory.recall_by_type(MemoryType.FACT)

# Recent memories (last 24 hours)  
recent = await memory.recall_recent(hours=24)

# Stats for debugging
stats = memory.get_embedding_stats()  # SemanticMemory only
```

## Architectural Boundaries

### What Memory DOES Handle
- ✅ Storage and retrieval of content
- ✅ Semantic similarity search
- ✅ Tag-based filtering and organization
- ✅ Time-based queries
- ✅ Type classification for different use cases

### What Memory DOES NOT Handle
- ❌ Automatic summarization (agent decides when/how)
- ❌ Session management (belongs in higher-level orchestration)
- ❌ Importance scoring (agent-driven via metadata)
- ❌ Conversation threading (chat state ≠ memory)
- ❌ Cognitive reasoning (memory is data infrastructure)

## Extension Points

Memory backends can be extended by implementing `BaseMemory`:

```python
class CustomMemory(BaseMemory):
    async def memorize(self, content: str, **kwargs) -> MemoryArtifact:
        # Custom storage logic
        pass
        
    async def recall(self, query: str, **kwargs) -> List[MemoryArtifact]:
        # Custom retrieval logic  
        pass
```

The interface supports arbitrary `kwargs` for backend-specific parameters without breaking the abstraction.

## Testing

Comprehensive test suite covers:
- Unit tests for each memory type and backend
- Integration tests for tool usage
- Parallel operation testing
- Edge cases and error handling
- Semantic search accuracy

Run tests:
```bash
poetry run pytest tests/memory/ -v
```

## Future Considerations

This architecture is designed to scale with agent complexity while maintaining clean primitives:

- Vector databases (pgvector, etc.) can implement `BaseMemory`
- Cross-agent memory sharing via networked backends
- Memory federation across multiple storage systems
- Advanced embedding strategies and similarity metrics

The key is that these extensions happen at the implementation level, not the interface level. Agents continue using the same clean primitives regardless of backend sophistication.