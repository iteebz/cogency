# Cogency Architecture Decisions

## Namespace Structure

### Core Primitives (Root Level)
```python
from cogency import reason, act
```

**Decision**: Reason and act are the two fundamental operations of any intelligent system. Root-level imports express this architectural truth.

### Core Architecture (LOCKED)
```
src/cogency/
├── context/         # Information assembly across domains
├── state/           # Data/persistence layer (31-field complexity)
├── reason/          # Think: context → decisions  
├── act/             # Do: decisions → results
├── tools/           # Tool definitions & execution (dual-role)
└── providers/       # LLM & embedding providers (auto-detection)
```

**Root-level primitives:**
```python
from cogency import reason, act  # Core execution primitives
```

### Additional Namespaces (Evaluation Results)
```
src/cogency/
├── memory/          # Memory and recall systems (LOCKED - user-scoped, dynamic)
├── knowledge/       # Knowledge extraction and retrieval (LOCKED - universal, static)
├── storage/         # Persistence backends
├── events/          # Event system and observability
├── semantic/        # Semantic search utilities (CONSOLIDATION TARGET)
├── cli/             # Command-line interface
```

**Decision**: Clean code organization with logical grouping, while maintaining simple public APIs.

### Context Assembly
```python
from cogency.context.assembly import build_context
```

**Domains**: `memory/`, `knowledge/`, `working/`, `conversation/`, `system/`

**Decision**: Context is assembled from multiple time horizons and sources. Domain separation for code clarity, unified assembly for LLM consumption.

### Execution Model
- **No separate execution namespace** - execution is context transformation
- **Tool duality accepted** - tools provide both context (schemas) and execution (actions)
- **ReAct pattern current** - but architecture supports future evolution

## Migration Strategy

**Approach**: Incremental namespace migration before state simplification
- Build new architecture foundation first
- Preserve existing functionality during transitions  
- A/B test new architecture vs old once infrastructure complete
- **Leave state/ simplification until last** for clean comparison

## Context Consolidation Strategy

**Decision**: Context wrappers were temporary setup - consolidate implementations into `context/`

### "Context is All You Need" Architecture  
```
src/cogency/
├── context/             # Context domain - all information implementations
│   ├── memory/          # Memory subdomain: Memory, Profile, MemorySystem + MemoryContext
│   ├── knowledge/       # Knowledge subdomain: extract, KnowledgeArtifact + KnowledgeContext  
│   ├── conversation/    # Conversation subdomain
│   ├── system/          # System subdomain
│   ├── working/         # Working state subdomain
│   └── assembly.py      # Context orchestration
├── tools/               # Pure action executors (CLI interfaces to context subdomains)
└── state/               # Minimal: IDs, timestamps, metadata only
```

**Terminology**: We use **domain/subdomain** (not namespace) moving forward.

**Principle**: Information retrieval belongs where it's consumed - in context assembly.

### Migration Phases
- **Phase 1**: Memory consolidation - move `memory/` → `context/memory/`
- **Phase 2**: Knowledge consolidation - move `knowledge/` → `context/knowledge/`  
- **Phase 3**: State minimization - reduce to persistence metadata only
- **Validation**: A/B test context-only vs 31-field legacy at each phase

## Migration Status
- ✅ Context namespace established and integrated
- ✅ `agents/` → `reason/` + `act/` migration complete
- ✅ Root-level `from cogency import reason, act` API working
- ✅ Core architecture locked: `context/`, `state/`, `reason/`, `act/`, `tools/`, `providers/`
- 🔄 **Phase 1**: Context consolidation - memory/ → context/memory/