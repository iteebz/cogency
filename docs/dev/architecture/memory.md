# Cogency Memory Architecture

**Canonical Memory System for Intelligent Agents**

## Research Context

Current agent frameworks suffer from goldfish memory: they lack genuine learning beyond conversation persistence. Existing approaches separate memory from cognition (mem0, RAG wrappers), conflate storage with learning (LangChain), or use flat storage without semantic structure (enterprise solutions).

Cogency integrates memory directly into agent reasoning processes.

## Overview

Dual-stream architecture: automatic context injection (profile) operates orthogonally to intentional knowledge retrieval. Agents maintain lean direct context while accessing accumulated learning on demand.

**Core Principle**: Memory and cognition are intertwined. Agents organize, synthesize, and evolve knowledge through reasoning processes rather than passive storage.

## Architecture Principles

**Orthogonal Memory Systems:**
- **Profile**: Automatic context injection (user identity, preferences, communication style)
- **Knowledge**: Intentional memory recall via tools (accumulated expertise and learning)

## State Components (Direct Context Injection)

### Profile
Persistent user identity, preferences, communication style.

### Conversation  
Current thread and recent message history.

### Workspace
Task-scoped insights, facts, observations. Archived on task completion.

### Execution
Runtime reasoning state. Never persisted.

## Knowledge Domain (Intentional Memory Recall)

Three-layer hierarchy:

### Layer 1: Topic Artifacts
**Hierarchical knowledge base organized like a docs/ folder**

```
memory/
  python/
    optimization-techniques.md
    async-patterns.md 
    testing-strategies.md
  react/
    performance-best-practices.md
    component-patterns.md
    state-management.md
  architecture/
    microservices-lessons.md
    database-design-principles.md
```

Accumulated expertise across conversations. Agents naturally organize knowledge hierarchically - semantic search across markdown files that grow, merge, and cross-reference over time.

### Layer 2: Thread Summaries
**Conversation outcomes and narrative memory**

Conversation outcomes and narrative memory. Key insights, decisions, and outcomes from completed conversations stored as structured summaries.

### Layer 3: Individual Messages
**Episodic recall of specific exchanges**

Episodic recall of specific exchanges. Every message indexed with vector embeddings for semantic similarity search.

## Retrieval Flow

### 1. Context Sufficiency Check
```python
direct_context = get_state_context(profile, conversation, workspace)
if direct_context.sufficient_for(query):
    proceed_with_reasoning(direct_context)
else:
    # Knowledge retrieval needed
    knowledge_context = recall_tool.search(query)
    proceed_with_reasoning(direct_context + knowledge_context)
```

### 2. Smart Layer Selection
- **Topic queries** → Search hierarchical knowledge docs
- **Outcome queries** → Search conversation summaries  
- **Specific references** → Search individual messages
- **Auto-detection** → Parse query intent to select appropriate layer(s)

### 3. Context Injection
Retrieved knowledge is injected alongside direct context, then discarded.

## Memory Daemon

Background process maintaining knowledge coherence:

### Compression Operations
**Compression:**
- Merge duplicate insights across conversations
- Combine scattered insights into coherent topic documents  
- Synthesize contradictory information with recency precedence

### Defragmentation
**Hierarchical Reorganization:**
```
# Before defrag:
memory/
  react/hooks.md
  javascript/react-patterns.md
  frontend/component-design.md

# After defrag:
memory/
  react/
    hooks.md (consolidated)
    patterns.md (merged from javascript)
    components.md (moved from frontend)
```

**Organization:**
- Link related concepts across topic boundaries
- Balance document sizes for optimal retrieval granularity
- Maintain topic relationship graphs

### Pruning Policies
**Pruning:**
- Archive unused knowledge
- Compress verbose exchanges into key insights
- Bounded storage growth with configurable retention

### Evolution Triggers
**Scheduling:**
- Daily: Compression and duplicate removal
- Weekly: Topic organization and cross-referencing  
- Monthly: Full defragmentation and restructuring
- Event-driven: New topic creation, contradiction resolution, pattern synthesis

## Implementation Phases

**Phase 1:** Topic artifacts with hierarchical markdown storage and semantic search.

**Phase 2:** Thread summaries capturing conversation outcomes.

**Phase 3:** Individual message indexing for episodic recall.

## Tool Interface

```python
class RecallTool(Tool):
    async def run(self, query: str, layer: str = "auto", limit: int = 3) -> str:
        # Auto-detect layer: messages (specific references), threads (outcomes), topics (knowledge)
        results = await self.knowledge.search(query, layer, limit, min_similarity=0.7)
        return self.format_results(results)

class Knowledge:
    async def search(self, query: str, layer: str, limit: int, min_similarity: float):
        # Layer-specific search with similarity threshold
        
    async def store_topic_insight(self, topic: str, insight: str, context: dict):
        # Hierarchical topic storage with vector indexing
```

## Storage Design

### Topic Artifacts
**File Structure:**
```markdown
# Python Optimization Techniques

## Last Updated
2025-01-15 - Consolidated async patterns from conversations #342, #389

## Key Insights

### Performance Patterns
- List comprehensions 2-3x faster than loops for simple operations
- `asyncio.gather()` optimal for concurrent I/O operations
- Caching with `@lru_cache` reduces repeated computation overhead

### Memory Management  
- Use `__slots__` for classes with many instances
- Generator expressions for large datasets
- `weakref` for breaking circular references

## Cross-References
- See also: [Async Best Practices](./async-patterns.md)
- Related: [Database Optimization](../database/query-optimization.md)

## Source Conversations
- #342: Performance debugging session (2025-01-10)
- #389: Memory optimization review (2025-01-14)
```

**Storage Schema:**
- **Format**: Markdown with YAML frontmatter
- **Indexing**: Vector embeddings per section + full document
- **Metadata**: `{created, updated, conversations, cross_refs, tags}`

### Thread Summaries  
**JSON Schema:**
```json
{
  "conversation_id": "uuid",
  "participants": ["user", "assistant"],
  "start_time": "2025-01-15T10:30:00Z",
  "duration_minutes": 45,
  "primary_topics": ["python", "optimization", "async"],
  "outcome_type": "problem_solved",  // problem_solved, learning, planning, debugging
  "key_insights": [
    "Identified N+1 query problem in ORM",
    "Implemented connection pooling solution",
    "Added monitoring for query performance"
  ],
  "artifacts_created": [
    "memory/database/query-optimization.md",
    "scripts/performance-monitor.py"
  ],
  "follow_up_actions": [
    "Monitor performance metrics for 1 week",
    "Consider implementing query caching"
  ],
  "narrative_summary": "User reported slow database queries. Investigation revealed N+1 problem in user profile loading. Implemented eager loading and connection pooling, resulting in 70% performance improvement."
}
```

**Storage:**
- **Format**: JSON with embedded narrative text
- **Indexing**: Vector embeddings of narrative_summary and key_insights
- **Location**: `memory/threads/{conversation_id}.json`

### Messages
**Database Schema:**
```sql
CREATE TABLE knowledge_messages (
    id UUID PRIMARY KEY,
    conversation_id UUID NOT NULL,
    role VARCHAR(20) NOT NULL,  -- user, assistant, system, tool
    content TEXT NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    metadata JSONB,  -- {tool_calls, context, reasoning_steps}
    embedding VECTOR(1536),  -- semantic search vector
    topic_tags TEXT[],  -- extracted topic associations
    INDEX idx_conversation (conversation_id),
    INDEX idx_timestamp (timestamp),
    INDEX idx_topics USING GIN (topic_tags)
);
```

**Indexing Strategy:**
- Individual message embeddings for precise recall
- Topic tag extraction for categorical search  
- Conversation grouping for context reconstruction
- Temporal indexing for chronological queries

## Performance Considerations

Layer-specific indices, query caching, and bounded search results. Incremental indexing with background daemon processing. Smart summarization and context prioritization (recent > accumulated knowledge).

## Human Inspectability

All accumulated knowledge is human-readable: markdown topic artifacts, JSON thread summaries, and queryable message records. Direct browsing, editing, and organization of agent knowledge.

## Future Considerations

Cross-conversation knowledge synthesis, temporal reasoning, forgetting mechanisms, and transfer learning between domains. Memory sharing between agents and integration with external knowledge sources.

## Success Metrics

Knowledge density, cross-reference connectivity, retrieval relevance, query response times, storage growth rates, and daemon processing efficiency.

## Research Implications

**Novel Contributions:**
1. Memory-cognition integration: Memory as active cognitive process, not passive storage
2. Hierarchical knowledge evolution: Automatic organization and refinement of expertise
3. Human-AI memory collaboration: Fully inspectable and editable knowledge base
4. Orthogonal memory streams: Clean separation of automatic vs intentional systems

**Architectural Advantages:**

**vs mem0:** Integrated cognition (not separated), hierarchical evolution (not flat storage)

**vs LangChain:** Multi-layer accumulation (not simple persistence), cross-conversation learning

**vs Enterprise:** Transparent and inspectable (not black-box), dynamic self-organization (not static)

**Future Research:** Memory reconsolidation during recall, dynamic knowledge weighting, temporal decay models, transfer learning between agents, causal reasoning, and predictive synthesis.

## Implementation Frontiers

The architecture presents several frontier challenges that distinguish cognitive memory systems from simple storage:

**Daemon Computational Costs:** Memory operations (synthesis, defragmentation, conflict resolution) require sophisticated reasoning rather than simple CRUD operations. Cost modeling and optimization strategies are essential for operational viability.

**Knowledge Synthesis Complexity:** Resolving contradictory information requires evaluating provenance, confidence, and context rather than naive recency precedence. This represents an AI-complete problem requiring advanced reasoning capabilities.

**Multi-Layer Query Routing:** Automatic layer selection and result fusion across Messages, Threads, and Topics requires intelligent classification and weighted relevance scoring. Complex queries may span multiple layers simultaneously.

**Human-Daemon Collaboration:** Manual editing of memory artifacts must coexist with automated daemon processes through version control-like conflict resolution, metadata locking mechanisms, and override policies.

**Cold Start Optimization:** New agents require seed knowledge or supervised accumulation phases to build initial topic artifacts before autonomous learning becomes effective.

These challenges represent the technical frontiers where breakthrough work in artificial memory systems occurs.

---

This architecture enables agents that genuinely learn and accumulate expertise over time - the first complete cognitive memory system for artificial intelligence.