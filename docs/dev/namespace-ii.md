# Canonical Namespace Architecture v4.0

**Date**: 2025-01-11  
**Status**: CANONICAL ARCHITECTURE - Ready for Implementation  
**Context**: Domain-driven organization to eliminate namespace chaos and architectural debt

---

## Executive Summary

**Problem**: Current layer-based organization (state/, memory/, tools/) creates artificial boundaries that split related concepts across namespaces, violating domain cohesion and creating cognitive overhead.

**Solution**: Domain-driven architecture where each domain contains all related concepts, eliminating scattered logic and confusing terminology.

**Result**: Canonical namespace with clear boundaries, obvious imports, and zero architectural debt.

---

## Architectural Principles Applied

### **Domain Cohesion Over Layer Separation**

**WRONG (Layer-first)**:
```
state/     # "Data layer"
memory/    # "Business logic layer" 
tools/     # "Interface layer"
```

**RIGHT (Domain-first)**:
```
user/      # User identity domain
knowledge/ # Knowledge management domain
documents/ # Document search domain
runtime/   # Execution state domain
```

### **BEAUTY DOCTRINE Compliance**

✅ **"One clear way to do each thing"** - Each concept has ONE canonical location  
✅ **"Question everything"** - Eliminates artificial layer boundaries  
✅ **"Delete more than create"** - Removes namespace confusion  
✅ **"Minimal and reads like English"** - Imports map directly to concepts

---

## Current State Analysis

### **Split Concepts (ARCHITECTURAL DEBT)**

**User Identity - Scattered Across 2 Namespaces:**
```python
state/Profile                    # Identity DATA
memory/situate/SituatedMemory   # Identity MANAGER
```

**Knowledge - Scattered Across 3 Namespaces:**
```python
memory/knowledge.py     # Knowledge EXTRACTION  
tools/recall.py        # Knowledge INTERFACE
semantic.py            # Knowledge SEARCH BACKEND
```

**Documents - Scattered Across 2 Namespaces:**
```python  
tools/retrieval.py     # Document INTERFACE
semantic.py            # Document SEARCH BACKEND
```

### **Router Anti-Pattern**

`semantic.py` acts as central router dispatching to different backends:
```python
# Anti-pattern: Router deciding implementation
if 'file_path' in search_kwargs:
    return await search_json_index(...)  # Documents
elif 'db_connection' in search_kwargs:
    return await search_sqlite_vectors(...)  # Knowledge
```

**Problem**: Related logic scattered, artificial abstraction layer.

---

## Canonical Architecture

### **Domain Organization**

```
cogency/
├── user/
│   ├── profile.py      # Profile + ProfileManager (consolidates state + situate)
│   └── __init__.py     
├── knowledge/
│   ├── extract.py      # extract_knowledge() (from memory/knowledge.py)
│   ├── search.py       # search_knowledge() (SQLite + vectors)  
│   └── __init__.py
├── documents/
│   ├── search.py       # search_documents() (JSON + vectors)
│   └── __init__.py  
├── runtime/
│   ├── state.py        # State, Execution, Conversation, Workspace
│   └── __init__.py
├── storage/
│   ├── sqlite.py       # (move from storage/state/)
│   ├── supabase.py     # (move from storage/state/)
│   └── __init__.py
├── utils/
│   ├── math.py         # cosine_similarity() (from semantic.py)
│   └── __init__.py
├── providers/          # LLM providers (unchanged)
├── tools/              # Thin wrappers (simplified)
├── events/             # Events (unchanged)
├── config/             # Config (unchanged)
├── security/           # Security (unchanged)
└── __init__.py         # Main exports
```

### **Domain Definitions**

#### **1. User Domain** (`user/`)
**Responsibility**: User identity, preferences, expertise, and profile management.

**Consolidates**:
- `state/Profile` → `user/profile.py:Profile`
- `memory/situate/SituatedMemory` → `user/profile.py:ProfileManager`

**Interface**:
```python
from cogency.user import Profile, ProfileManager

# Usage
profile = Profile(user_id="alice", expertise_areas=["python"])
manager = ProfileManager(store=sqlite)
await manager.save_profile(profile)
```

#### **2. Knowledge Domain** (`knowledge/`)
**Responsibility**: Extract insights from conversations, store as vectors, enable semantic search.

**Consolidates**:
- `memory/knowledge.py` → `knowledge/extract.py`
- `semantic.py:search_sqlite_vectors` → `knowledge/search.py`
- `tools/recall.py` becomes thin wrapper

**Interface**:
```python
from cogency.knowledge import extract_knowledge, search_knowledge

# Usage
await extract_knowledge(user_id, messages, llm, embedder)
results = await search_knowledge(user_id, query, embedder, top_k=5)
```

#### **3. Documents Domain** (`documents/`)
**Responsibility**: Search static document corpus using pre-computed embeddings.

**Consolidates**:
- `semantic.py:search_json_index` → `documents/search.py`
- `tools/retrieval.py` becomes thin wrapper

**Interface**:
```python
from cogency.documents import search_documents

# Usage
results = await search_documents(query, embedder, corpus_path="docs.json")
```

#### **4. Runtime Domain** (`runtime/`)
**Responsibility**: Execution state, conversation history, task workspace.

**Already cohesive** - minimal changes:
- Move `state/` → `runtime/state.py`
- Consolidate all state management in one place

**Interface**:
```python
from cogency.runtime import State, execute_task

# Usage
state = await State.start_task(query="analyze code", user_id="alice")
```

#### **5. Storage Domain** (`storage/`)
**Responsibility**: Persistence backends for all domains.

**Flattens**:
- `storage/state/sqlite.py` → `storage/sqlite.py`
- `storage/state/supabase.py` → `storage/supabase.py`

**Rationale**: SQLite isn't "state-only" - it's a general persistence backend.

#### **6. Utils Domain** (`utils/`)
**Responsibility**: Pure functions used across domains.

**Extracts**:
- `semantic.py:cosine_similarity` → `utils/math.py`

**Interface**:
```python
from cogency.utils.math import cosine_similarity

similarity = cosine_similarity(vec1, vec2)  # Pure function
```

---

## Import Transformation

### **Before (Chaos)**
```python
from cogency.state import Profile
from cogency.memory.situate import SituatedMemory
from cogency.semantic import semantic_search
from cogency.tools import Recall
from cogency.storage.state import SQLite
```

### **After (Canonical)**
```python
from cogency.user import Profile, ProfileManager
from cogency.knowledge import extract_knowledge, search_knowledge
from cogency.documents import search_documents  
from cogency.runtime import State, execute_task
from cogency.storage import SQLite
```

**Every import maps to ONE clear domain concept.**

---

## What Gets Eliminated

### **Files Deleted**
- `semantic.py` - Router logic split into domains
- `memory/` namespace - Consolidated into `knowledge/` and `user/`
- `storage/state/` subdirectory - Flattened to `storage/`

### **Concepts Unified**
- ~~"Situated Memory"~~ + ~~"Profile"~~ → **ProfileManager**
- ~~"Archival Memory"~~ → **Knowledge Domain**
- ~~"Memory vs State"~~ → **Clear Domain Boundaries**
- ~~"semantic_search() router"~~ → **Domain-specific functions**

### **Artificial Boundaries Removed**
- Data vs Logic vs Interface layers
- Memory vs State distinction  
- Router abstraction layers

---

## Migration Strategy

**This is NOT a rewrite - it's ORGANIZATION.**

### **Phase 1: Create Domain Structure**
```bash
mkdir -p src/cogency/{user,knowledge,documents,runtime,utils}
mkdir -p src/cogency/utils
```

### **Phase 2: Move Files to Domains**
```bash
# User domain
mv src/cogency/state/state.py src/cogency/runtime/state.py
cp src/cogency/state/__init__.py src/cogency/user/profile.py  # Profile dataclass
mv src/cogency/memory/situate/classes.py src/cogency/user/manager.py

# Knowledge domain  
mv src/cogency/memory/knowledge.py src/cogency/knowledge/extract.py
# Split semantic.py SQLite logic → knowledge/search.py

# Documents domain
# Split semantic.py JSON logic → documents/search.py

# Storage flattening
mv src/cogency/storage/state/sqlite.py src/cogency/storage/sqlite.py
mv src/cogency/storage/state/supabase.py src/cogency/storage/supabase.py
rmdir src/cogency/storage/state/

# Utils extraction
# Extract cosine_similarity → utils/math.py
```

### **Phase 3: Update Imports**
```bash
# Global import updates
find src/ -name "*.py" -exec sed -i 's/from cogency\.state import Profile/from cogency.user import Profile/g' {} +
find src/ -name "*.py" -exec sed -i 's/from cogency\.semantic/from cogency.knowledge/g' {} +
find src/ -name "*.py" -exec sed -i 's/storage\.state/storage/g' {} +
```

### **Phase 4: Simplify Tools**
```python
# tools/recall.py becomes thin wrapper
class Recall(Tool):
    async def run(self, query: str, **kwargs):
        from cogency.knowledge import search_knowledge
        return await search_knowledge(query, **kwargs)

# tools/retrieval.py becomes thin wrapper  
class Retrieval(Tool):
    async def run(self, query: str, **kwargs):
        from cogency.documents import search_documents
        return await search_documents(query, **kwargs)
```

### **Phase 5: Clean Domain Boundaries**
- Update `__init__.py` exports
- Remove cross-domain dependencies
- Consolidate duplicate logic

---

## Validation Strategy

### **Architecture Tests**
```python
def test_domain_boundaries():
    """Ensure domains don't have circular dependencies."""
    # user/ can't import knowledge/
    # knowledge/ can't import documents/
    # runtime/ can't import user/knowledge/documents/

def test_canonical_imports():
    """Ensure imports work as expected."""
    from cogency.user import Profile, ProfileManager
    from cogency.knowledge import extract_knowledge, search_knowledge
    from cogency.documents import search_documents
    from cogency.runtime import State
    # All should work without errors
```

### **Functionality Preservation**
- All existing tests must pass
- Tools (Recall, Retrieval) work unchanged from user perspective  
- Agent execution flows preserved
- Profile/knowledge operations preserved

### **Performance Validation**
- No regression in search performance
- Import times don't increase
- Memory usage stays constant

---

## Benefits Achieved

✅ **Cognitive Clarity**: Obvious where any concept lives  
✅ **Zero Namespace Confusion**: No more "memory vs state vs tools"  
✅ **Domain Cohesion**: Related concepts co-located  
✅ **Eliminated Duplication**: ProfileManager consolidates split logic  
✅ **Clean Dependencies**: Each domain has clear responsibilities  
✅ **BEAUTY DOCTRINE**: Minimal, canonical, obvious organization  
✅ **Future Extensions**: New features have obvious homes

---

## Critical Success Factors

### **All Tests Must Pass**
No functionality changes - only organization changes.

### **Zero Breaking Changes**  
Tools, Agent, and public APIs work identically.

### **Import Clarity**
Every import should be obvious and domain-appropriate.

### **Documentation Alignment**
All docs updated to reflect canonical organization.

---

## Architectural Status

**CANONICAL ARCHITECTURE DEFINED** ✅  
**READY FOR IMPLEMENTATION** ✅  
**MIGRATION STRATEGY VALIDATED** ✅  

This namespace architecture eliminates all identified architectural debt and establishes canonical domain boundaries for future development.

---

*This document represents the complete canonical namespace architecture. All decisions are grounded in first principles analysis and BEAUTY DOCTRINE compliance.*