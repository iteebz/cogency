# Changelog

## [1.2.0] - 2025-08-09
**Provider Ecosystem + RAG**

- **OpenRouter & Groq LLM providers** - Cost-effective routing + high-performance inference
- **Canonical Retrieval tool** - Semantic search, lazy indexing, multi-format support
- **Configurable caching** - TTL/size parameters in provider base classes
- **Data-driven defaults** - Model selection from 537B+ token usage statistics
- **Provider status**: 7/7 LLM, 3/3 Embed working (100% coverage)

## [1.1.0] - 2025-08-08
**Three-Horizon State Architecture**

**BREAKING**: Complete state redesign
- **Split-state model** - UserProfile (permanent) / Workspace (task) / ExecutionState (runtime)
- **Database-as-state** - SQLite schema matches dataclass structure
- **Mutation API** - `add_message()`, `learn_insight()` replace direct manipulation
- **ACID transactions** - Task isolation with automatic cleanup
- **Built-in observability** - `@observe` decorator on all core steps

## [1.0.1] - 2025-08-07
- Fixed OpenAI rate limit retry method names
- Added missing base class attributes for embedding providers

## [1.0.0] - 2025-08-03
**Production Release**

**BREAKING**: Complete rewrite from v0.9.x
- **Security framework** - Multi-layered LLM threat detection
- **API simplification** - `AgentBuilder` → direct `Agent()` construction
- **Evaluation suite** - 379 tests across 15 suites
- **Memory synthesis** - Compression and synthesis capabilities
- **Ollama support** - Local model integration

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

**Pace**: 16 releases in 1 month. 296 commits. 3 complete rewrites.