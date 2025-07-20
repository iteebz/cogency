# Changelog

All notable changes to this project will be documented in this file.

## v0.5.1 - Rearchitect + Coding Agent
*July 20, 2025*

**Decomposed nodes, zero ceremony, working coding agent.** Complete architectural overhaul with node decomposition, simplified execution, and expanded tool ecosystem.

### ✨ New Features
- **Coding Agent** - Production-ready coding assistant with file editing capabilities
- **Emoji Messaging** - Beautiful emoji-based communication system for enhanced UX
- **Extended Tool Suite** - Shell, code execution, HTTP requests, datetime, CSV, SQL tools
- **Expression Calculator** - Smart mathematical expression evaluation
- **Identity Prompting** - Enhanced personality and identity management

### 🔧 Developer Experience
- **Zero Ceremony** - Eliminated unnecessary abstractions and complexity
- **Simplified Testing** - Complete test suite rewrite with focused, maintainable tests
- **Graceful Error Handling** - Improved resilience and error recovery
- **Clean Tool Execution** - Streamlined tool discovery and execution pipeline

### 🏗️ Architecture
- **Node Decomposition** - Split monolithic ReAct into focused nodes (preprocess, reason, act, respond)
- **Eliminated Antipatterns** - Removed over-engineered abstractions and ceremonial code
- **Codebase Reorganization** - Flattened module structure with logical separation
- **Simplified Memory** - Streamlined CRUD operations with standardized backends
- **Removed Complexity Analysis** - Eliminated adaptive reasoning heuristics for LLM preprocessing

### 🗑️ Removed
- **Adaptive Reasoning** - Replaced complex heuristics with LLM-based preprocessing
- **Monitoring Overhead** - Removed unnecessary alerts, collectors, and monitoring ceremony
- **Over-Engineering** - Eliminated abstract base classes and complex inheritance hierarchies
- **Legacy Tests** - Nuked 9,500+ lines of overcomplicated test code

---

## v0.5.0 - Memory & Personality
*July 18, 2025*

**Extensible memory + beautiful tracing.** Advanced memory backends, personality system, and clean phase tracing.

### ✨ New Features
- **Memory Backends** - Pinecone, ChromaDB, and PGVector support with semantic search
- **Personality Prompting** - Magical personality, tone, and style injection system
- **Clean Phase Tracing** - Beautiful `👤 HUMAN:` and `🤖 AGENT:` formatted output
- **Pre-ReAct Prepare Node** - Enhanced tooling and memory phases
- **Multi-Tenancy** - User-isolated conversations and memory management

### 🔧 Developer Experience
- **Auto-Tag Memories** - Intelligent memory categorization and retrieval
- **Import Extras** - Streamlined optional dependency management
- **MCP Server** - Model Context Protocol integration
- **Comprehensive Testing** - Enhanced test coverage and reliability

### 🏗️ Architecture
- DRY memory backend implementations with consistent interfaces
- Response shaping and conversation history management
- Decomposed ReAct loop with pluggable memory systems
- Optional dependency handling and graceful degradation

---

## v0.4.1 - Streaming DX
*July 16, 2025*

**Developer experience polish.** Minor improvements to streaming experience and documentation.

### 🔧 Developer Experience
- **Enhanced Marketing** - Updated messaging and positioning
- **Repository Cleanup** - Removed legacy files and improved organization
- **Documentation Polish** - Minor fixes and improvements

---

## v0.4.0 - ReAct & Production Ready
*July 16, 2025*

**Architecture revolution.** Complete transition from PRARR to ReAct with enterprise-grade production features.

### ✨ New Features
- **ReAct Architecture** - Migrated from PRARR to industry-standard ReAct loop (Reason → Act → Observe)
- **Production Hardening** - Metrics, resilience, and enterprise-grade reliability
- **Parallel Tool Execution** - Concurrent tool calls with robust error handling
- **Smart Memory** - Relevance scoring and intelligent memory management
- **Infinite Loop Detection** - Built-in protection against reasoning cycles

### 🔧 Developer Experience
- **Golden Trace Validation** - Reference traces for testing and debugging
- **Adaptive Reasoning Depth** - Dynamic reasoning complexity based on query
- **Enhanced Tracing** - Improved visibility into reasoning steps
- **Tool Filtering** - Intelligent tool selection and result processing

### 🏗️ Architecture
- Complete ReAct loop implementation with streaming support
- Concurrency-safe state coordination
- Pluggable cognitive nodes architecture
- Memory primitives and embedding providers
- Comprehensive production testing suite

---

## v0.3.0 - Streaming Revolution
*July 12, 2025*

**Stream-first architecture.** Complete overhaul to real-time streaming execution with universal LLM support.

### ✨ New Features
- **Stream-First Execution** - All nodes redesigned as async generators for real-time visibility
- **Universal LLM Support** - OpenAI, Anthropic, Gemini, Grok, Mistral with native streaming
- **Agent.stream()** - New streaming method for real-time execution transparency
- **Conversation History** - Built-in conversation state management
- **Nomic Embeddings** - Advanced embedding provider integration

### 🔧 Developer Experience
- **Async by Default** - Full async/await architecture throughout
- **Cancellation Support** - Graceful interruption with @cancellation decorator
- **Comprehensive Testing** - 47+ streaming tests and robust coverage
- **Security Policy** - Formal security guidelines and practices

### 🏗️ Architecture
- Native LLM streaming for all providers
- Standardized configuration and error handling
- Stream-first node architecture (plan_streaming, reason_streaming, etc.)
- Enhanced context management and state coordination

---

## v0.2.3 - DDGS Compatibility
*July 12, 2025*

**Compatibility fix.** Updated DuckDuckGo Search integration for latest API changes.

### 🔧 Fixed
- **DDGS Integration** - Updated web search tool for latest DuckDuckGo API
- **Documentation** - Updated examples and usage patterns
- **Dependencies** - Cleaned up dependency versions and compatibility

### 🏗️ Architecture
- Improved web search reliability and error handling
- Enhanced test coverage for search functionality

---

## v0.2.2 - Live Traces
*July 12, 2025*

**Real-time visibility.** Live trace streaming, implicit key rotation, and comprehensive stability improvements.

### ✨ New Features
- **Live Trace Streaming** - Real-time execution visibility as agents think
- **Implicit Key Rotation** - Automatic LLM key management and failover
- **Stability Improvements** - Enhanced error handling and parsing robustness

### 🔧 Developer Experience
- **Enhanced Examples** - Updated documentation and usage patterns
- **Infinite Recursion Detection** - Built-in protection against runaway loops
- **Parsing Robustness** - Better handling of malformed LLM responses

### 🏗️ Architecture
- Improved context management and state handling
- Enhanced trace formatting and output processing
- Comprehensive test coverage for edge cases

---

## v0.2.1 - Developer Experience
*July 12, 2025*

**Polish and power.** Enhanced tooling, better LLM architecture, and improved developer experience.

### ✨ New Features
- **File Manager Tool** - Read, write, and manage files with built-in validation
- **Modular LLM Architecture** - Split LLM providers into separate modules
- **Trace Control** - Optional trace printing with configurable output

### 🔧 Developer Experience  
- **Stabilized Prompts** - More consistent and reliable prompt engineering
- **Enhanced Examples** - Custom tool examples with file management
- **Better Error Handling** - Improved trace extraction and formatting

### 🏗️ Architecture
- Separated LLM providers (Gemini, key rotation) for better extensibility
- Cleaner tool registration and discovery
- Improved test coverage and organization

---

## v0.2.0 - Core Framework
*July 12, 2025*

**The foundation.** First production-ready release with custom PRARR architecture and comprehensive tool ecosystem.

### ✨ New Features
- **PRARR Architecture** - Plan → Reason → Act → Reflect → Respond cognitive loop
- **Tool System** - Web search, calculator with auto-discovery and validation  
- **Execution Tracing** - Full transparency into agent reasoning steps
- **LLM Orchestration** - OpenAI integration with key rotation and caching
- **CLI Interface** - Basic command-line agent interaction

### 🔧 Developer Experience
- **115 Unit Tests** - Comprehensive test coverage across all components
- **Clean API** - Simple Agent class with context management
- **JSON Routing** - Structured tool calls and response parsing

### 🏗️ Architecture
- Central tool registry with automatic discovery
- Multiline prompt engineering with clean formatting
- Robust error handling and output validation