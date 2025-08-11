# Phase 1 Archival Memory Implementation

**Status**: Production Ready  
**Architecture**: Procedural Pipeline (AI Council Approved)  
**Implementation**: Complete  

## Overview

Topic-based archival memory system for accumulating knowledge artifacts across conversations. Uses LLM-based topic extraction with procedural consolidation pipeline for reliability.

## Architecture Principles

**Infrastructure over Intelligence**: Archival consolidation is a data processing pipeline, not a reasoning task. Uses deterministic stages with explicit error handling rather than fractal agents.

**Single LLM Consolidation**: Archive step extracts knowledge artifacts from conversation history at finalization, separate from profile updates.

**Conservative Thresholds**: 0.8+ similarity for document merging, 0.7+ confidence for knowledge acceptance - prioritizes precision over recall.

## Implementation Flow

### 1. Archive Trigger
**Location**: `state/state.py:finalize()`  
**Trigger**: Conversation end via finalize() lifecycle hook  
**Input**: Full conversation history from state  

### 2. Knowledge Extraction  
**Location**: `memory/archive/prompt.py:EXTRACTION_SYSTEM_PROMPT`  
**Output**: 
```json
{
  "knowledge": [
    {
      "topic": "Python Optimization",
      "knowledge": "List comprehensions are 2-3x faster than for loops",
      "confidence": 0.9,
      "context": "performance discussion"
    }
  ]
}
```

### 3. Knowledge Processing
**Location**: `memory/archive/core.py:_process_knowledge()`  
**Pipeline**: For each knowledge item extracted:

#### Stage 1: Quality Validation
```python
def _meets_quality_threshold(knowledge: Dict) -> bool:
    return (
        len(knowledge.get("knowledge", "")) > 20 and
        knowledge.get("confidence", 0) > 0.7 and
        knowledge.get("topic", "").strip() != "" and
        knowledge.get("topic", "").lower() not in ["general", "misc", "other", "unknown"]
    )
```

#### Stage 2: Semantic Search
```python
similar_docs = await archival.search_topics(
    user_id=user_id,
    query=topic,
    limit=3,
    min_similarity=0.8  # Conservative threshold
)
```

#### Stage 3: Deterministic Merge Decision
```python
if similar_docs:
    # Always merge with highest similarity document
    target_doc = max(similar_docs, key=lambda doc: doc["similarity"])
    await _merge_with_existing(knowledge, target_doc, archival, user_id)
else:
    # Create new document
    await archival.store_knowledge(user_id, topic, knowledge_content)
```

### 4. Document Merging
**Location**: `memory/archive/core.py:_merge_with_existing()`  
**Strategy**: One LLM call per document merge with specialized prompt  

```
Existing Document + New Knowledge → Specialized Merge Prompt → Updated Document
```

**Merge Instructions**:
- Integrate naturally, avoid duplication
- Note contradictory perspectives with context  
- Maintain markdown structure
- Update metadata timestamps

### 5. Filesystem Persistence
**Location**: `memory/archival.py:_save_merged_topic()`  
**Format**: Markdown files with YAML frontmatter  
**Path**: `~/.cogency/memory/{user_id}/topics/{topic-name}.md`  

## Error Handling

### Structured Errors
```python
class ConsolidationError(Exception):
    def __init__(self, message: str, stage: str):
        self.stage = stage  # "validation", "search", "merge"
```

### Failure Modes
- **Quality validation fails** → Skip knowledge item, continue with others
- **Semantic search fails** → Create new document instead of merging
- **Document merge fails** → Fallback to new document creation
- **Entire consolidation fails** → Graceful degradation, user experience unaffected

### Observable Pipeline
```python
emit("archival", operation="knowledge_processing", 
     user_id=user_id, topic=topic, stage="validated")
emit("archival", operation="document_merge",
     user_id=user_id, stage="complete", merged_length=len(content))
```

## File Structure

```
src/cogency/
├── memory/situate/      # Profile update step
│   ├── core.py         # Situate step logic
│   ├── profile.py      # Profile synthesis utilities
│   └── prompt.py       # Profile update prompts
├── memory/archive/      # Knowledge extraction step
│   ├── core.py         # Archive step logic
│   └── prompt.py       # Knowledge extraction prompts
└── memory/
    ├── archival.py      # Topic artifact storage & search
    └── synthesizer.py   # Integration point (archival methods deprecated)
```

## Key Functions

### Archive Integration
- `memory/archive/core.py:archive()` - Main entry point
- `memory/archive/core.py:_extract_knowledge()` - Knowledge extraction

### Quality Control  
- `memory/archive/core.py:_meets_quality_threshold()` - Knowledge validation
- `memory/archive/core.py:_process_knowledge()` - Per-knowledge pipeline

### Document Operations
- `memory/archival.py:search_topics()` - Semantic similarity search
- `memory/archival.py:_save_merged_topic()` - Filesystem persistence
- `memory/archival.py:store_knowledge()` - New document creation

## Storage Schema

### Topic Artifacts
```markdown
---
topic: "Python Optimization"
created: "2025-01-15T10:30:00Z" 
updated: "2025-01-20T15:45:00Z"
source_conversations: ["conv-123", "conv-456"]
---

# Python Optimization

## Performance Patterns
- List comprehensions 2-3x faster than loops for simple operations
- `asyncio.gather()` optimal for concurrent I/O operations

## Memory Management
- Use `__slots__` for classes with many instances
- Generator expressions for large datasets

*Last updated: 2025-01-20*
```

### Search Index
- **Vector embeddings** per document for semantic similarity
- **Cosine similarity** calculation for document matching
- **In-memory cache** for performance (`_embedding_cache`)

## Configuration

### Thresholds
```python
QUALITY_MIN_LENGTH = 20          # Minimum knowledge character length
QUALITY_MIN_CONFIDENCE = 0.7     # Minimum confidence score
SEMANTIC_MIN_SIMILARITY = 0.8    # Document merge threshold
SYNTHESIS_TRIGGER_COUNT = 3      # Interactions between synthesis
```

### File Paths
```python
BASE_PATH = "~/.cogency/memory"
USER_PATH = "{BASE_PATH}/{user_id}/topics"  
TOPIC_FILE = "{USER_PATH}/{sanitized-topic-name}.md"
```

## Testing

### Quality Gates
```python
# Valid knowledge
{
  "topic": "Python Performance",
  "knowledge": "List comprehensions outperform for loops by 2-3x for simple iterations",
  "confidence": 0.9,
  "context": "optimization discussion"
}

# Invalid knowledge (filtered out)
{
  "topic": "general",           # Generic topic
  "knowledge": "Short",          # Below 20 chars  
  "confidence": 0.6,           # Below 0.7 threshold
  "context": "brief mention"
}
```

### Pipeline Validation
```bash
poetry run python -c "
from cogency.steps.synthesize.archival import _meets_quality_threshold
result = _meets_quality_threshold({'knowledge': 'Valid knowledge content', 'confidence': 0.8, 'topic': 'Python'})
print(f'Quality check: {result}')  # Should be True
"
```

## Context Transfer Notes

**For Future Development**:
- Phase 2: Thread summary storage (conversation outcomes)
- Phase 3: Individual message indexing (episodic recall)
- Potential optimization: Batch document merging for related topics
- Monitoring: Add metrics for consolidation success rates, document growth

**Key Design Decisions**:
- Procedural over fractal agents (AI Council recommendation)
- Conservative similarity thresholds (reliability over coverage)  
- Single LLM call consolidation (cost efficiency)
- Per-document merging (error isolation)