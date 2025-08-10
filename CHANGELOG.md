# Changelog

## [1.2.2] - 2025-08-10
- **Four-component state** - Added Conversation component for message persistence
- **Stream buffer retry** - Automatic LLM streaming failure recovery
- **File vector store** - Local semantic search
- **Provider key rotation** - High-volume API key cycling

## [1.2.1] - 2025-08-09
- **8 production providers** - Unified LLM + embedding base class
- **Semantic parameters** - `llm_model`/`embed_model` naming

## [1.2.0] - 2025-08-09
- **OpenRouter + Groq** providers
- **Retrieval tool** - Semantic search, lazy indexing
- **Provider caching** - Configurable TTL/size

## [1.1.0] - 2025-08-08
**BREAKING**: Complete state redesign
- **Three-component state** - Profile/Workspace/ExecutionState persistence layers
- **Database-as-state** - SQLite schema matches dataclasses
- **Mutation API** - `add_message()`, `learn_insight()` functions

## [1.0.1] - 2025-08-07
- OpenAI rate limit fixes
- Embedding provider base class fixes

## [1.0.0] - 2025-08-03
**BREAKING**: Complete rewrite
- **Security framework** - Multi-layered LLM threat detection
- **Direct Agent()** construction
- **311 tests** - Full evaluation suite
- **Memory synthesis** - Compression capabilities
- **Ollama support** - Local models

---

## Development History (v0.9.x → v0.1.0)

**v0.9.3** (2025-08-01) - Module reorganization, `services/` → `providers/`, removed 8 specialized tools
**v0.9.2** (2025-07-31) - Cross-provider benchmarking, timing utilities
**v0.9.1** (2025-07-31) - Memory persistence, observability exports
**v0.9.0** (2025-07-30) - Custom ReAct implementation, 290+ tests, resilience modules

**v0.5.1** (2025-07-20) - Coding agent, extended tools, architectural overhaul
**v0.5.0** (2025-07-18) - Memory backends (Pinecone, ChromaDB), personality system
**v0.4.0** (2025-07-16) - PRARR → ReAct migration, production hardening
**v0.3.0** (2025-07-12) - Stream-first architecture, universal provider support
**v0.2.x** (2025-07-12) - Tool system, trace streaming, key rotation
**v0.1.0** (2025-07-10) - Experimental skills-based agent framework

Key architectural evolution:
- **0.1-0.2**: Basic PRARR framework
- **0.3-0.4**: ReAct migration, streaming architecture  
- **0.5-0.9**: Memory systems, provider ecosystem, testing
- **1.0+**: Production stability, security, state management

---

**18 releases • 308 commits • 1 month**