# Cogency Architecture Decisions

## Namespace Structure

### Core Primitives (Root Level)
```python
from cogency import reason, act
```

**Decision**: Reason and act are the two fundamental operations of any intelligent system. Root-level imports express this architectural truth.

### Internal Organization
```
src/cogency/
├── reason/          # Think: context → decisions
├── act/             # Do: decisions → results  
├── context/         # Context assembly across domains
├── tools/           # Tool definitions and registry
├── memory/          # Memory and recall systems
├── knowledge/       # Knowledge extraction and retrieval
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

## Migration Status
- ✅ Context namespace established  
- ✅ `agents/` → `reason/` + `act/` migration complete
- ✅ Root-level `from cogency import reason, act` API working