# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.1] - 2025-08-07

### Fixed
- **OpenAI Provider**: Fixed method name mismatch in rate limit retry calls (`with_rate_limit_retry` → `retry_rate_limit`)
- **Embedding Providers**: Added missing `_should_retry` and `key_rotator` attributes to base `Embed` class

## [1.0.0] - 2025-08-03

**MILESTONE**: First stable production release with locked API surface

**WARNING**: Complete architectural rewrite - no backward compatibility with v0.9.x

### Major Changes
- **Security Framework**: Multi-layered LLM-based threat detection with prompt injection prevention, command injection validation, and sensitive information sanitization
- **State Architecture**: Monolithic `state.py` and `memory.py` modules redesigned as modular packages
- **CLI Interface**: Production-ready interactive agent commands  
- **Evaluation Suite**: Comprehensive testing framework with 379 tests across 15 suites
- **API Simplification**: Removed `AgentBuilder` - back to direct `Agent()` construction
- **Memory Synthesis**: New memory compression and synthesis capabilities

### Breaking Changes
- No backward compatibility with v0.9.x
- `AgentBuilder().name("x").build()` → `Agent("x")`
- `prepare` step renamed to `triage` 
- State/memory imports require new modular structure
- Timer/token utilities moved from `utils/` to `observe/`
- Legacy evaluation suite replaced with task-based system

### New Features
- Ollama provider support for local models
- Provider auto-detection with lazy loading
- Memory synthesis and compression
- Enhanced tool security validation
- Defense-in-depth security architecture

## [0.9.3] - 2025-08-01

### Added
- New `ask` tool for human-in-the-loop interactions
- Enhanced agent constructor with builder pattern
- Decomposed preprocessing pipeline with modular components

### Changed
- **BREAKING**: Complete module reorganization for better separation of concerns
- **BREAKING**: `services/` renamed to `providers/` for LLM and embedding providers
- **BREAKING**: `phases/` restructured as `steps/` with cleaner cognitive workflow
- **BREAKING**: Configuration system redesigned with dedicated `config/` module
- **BREAKING**: Execution engine refactored (`executor.py` → `runtime.py`)
- **BREAKING**: Streamlined tool suite - removed 8 specialized tools in favor of core functionality
- Evaluation framework moved to project root with improved structure
- Memory system flattened for simpler architecture
- Enhanced steps architecture: `prepare/`, `reason/`, `act/`, `respond/`
- Improved error handling and execution flow
- Streamlined codebase with 2,171 net lines removed across all commits

### Removed
- **BREAKING**: MCP (Model Context Protocol) server functionality
- **BREAKING**: XAI provider support 
- **BREAKING**: Specialized tools: `calculator`, `csv`, `date`, `scrape`, `shell`, `sql`, `time`, `weather`
- Complex reasoning switching logic in favor of simpler patterns
- Redundant utility modules and abstractions
- Over-engineered configuration patterns
- Deprecated parsing utilities

### Migration Guide
- Update imports: `cogency.services.*` → `cogency.providers.*`
- Update imports: `cogency.phases.*` → `cogency.steps.*`
- Replace `cogency.executor` imports with `cogency.runtime`
- Update configuration usage for new `config/` module structure
- Remove MCP server usage (no longer supported)
- Replace removed tools (`calculator`, `csv`, `date`, `scrape`, `shell`, `sql`, `time`, `weather`) with equivalent functionality or external libraries

## [0.9.2] - 2025-07-31

### Added
- Cross-provider benchmarking framework for systematic model comparison
- Timing benchmarks to measure agent performance across workloads
- Timer utility functions for built-in performance measurement
- Comprehensive eval framework with provider comparison tools

### Changed
- Optimized execution pipeline with early response pattern for reduced latency
- Cost-efficient model defaults for common tasks
- Better separation of concerns in phase management
- Refactored benchmarking system with modular architecture

### Fixed
- Phase ordering issues that caused unnecessary delays
- Minor execution flow inefficiencies

## [0.9.1] - 2025-07-31

### Added
- Situated memory architecture with direct context injection
- Cross-session memory persistence via store integration  
- LLM-native state schema validation
- Prometheus and OpenTelemetry exporters for observability
- Memory session management and restoration

### Changed
- Streamlined documentation structure
- Updated website copy and positioning

### Fixed
- Memory persistence edge cases
- Documentation inconsistencies

## [0.9.0] - 2025-07-30

### Added
- Canonical ReAct cognitive architecture implementation
- Comprehensive validation suite with 290+ tests
- Resilience module: retry/timeout, circuit breaks and rate-limiting
- Robust module: includes resilience, checkpoints and recovery
- Observe module: monitoring and metrics
- Filesystem-based state persistence
- Dispatch notifier: event-driven, decoupled notifier logic
- Auto-detection for LLM and embedding providers
- Explicit tool schema validation without reflection

### Changed
- Migrated from LangGraph to custom ReAct implementation
- Standardized singleton patterns across providers
- Unified reasoning prompts and flags
- Moved LLM cache to improve performance
- Simplified response flow and eliminated ceremony

### Fixed
- Formatting corruption and test failures
- Auto provider key detection issues
- Checkpointing restoration
- Deep reasoning mode functionality

### Removed
- LangGraph dependency and related abstractions
- Action fingerprinting complexity
- Tool formatting ceremony

## [0.5.1] - 2025-07-20

### Added
- Coding agent with file editing capabilities
- Emoji-based messaging system
- Extended tool suite: shell, code execution, HTTP requests, datetime, CSV, SQL
- Code execution
- Identity and personality prompting system

### Changed
- **BREAKING**: Complete architectural overhaul with node decomposition
- **BREAKING**: Split monolithic ReAct into focused phases (prepare, reason, act, respond)
- **BREAKING**: Eliminated adaptive reasoning heuristics in favor of LLM preparing
- **BREAKING**: Flattened module structure and reorganized codebase
- **BREAKING**: Replaced complex inheritance hierarchies with simpler patterns
- Standardized CRUD memory backend operations
- Simplified testing framework (removed 9,500+ lines of test code)
- Enhanced error handling and resilience patterns

### Removed
- **BREAKING**: Adaptive reasoning complexity analysis
- **BREAKING**: Monitoring overhead and ceremony
- **BREAKING**: Abstract base classes and over-engineered patterns
- Legacy test suite (complete rewrite)

### Migration Guide
- Update import paths due to module reorganization
- Replace adaptive reasoning calls with LLM preparing
- Migrate from old node structure to new phase-based architecture
- Update tool registration to use new simplified API

## [0.5.0] - 2025-07-18

### Added
- Memory backends: Pinecone, ChromaDB, PGVector with semantic search
- Personality prompting system for tone and style injection
- Clean phase tracing with formatted output (`👤 HUMAN:` / `🤖 AGENT:`)
- Pre-ReAct prepare phase for enhanced tooling
- Multi-tenancy with user-isolated conversations
- Auto-tagging for intelligent memory categorization
- MCP (Model Context Protocol) server integration

### Changed
- **BREAKING**: Decomposed ReAct loop with pluggable memory systems
- DRY memory backend implementations with consistent interfaces
- Enhanced conversation history management
- Improved optional dependency handling

### Fixed
- Memory unit test failures and reliability issues
- Optional dependency import errors

## [0.4.1] - 2025-07-16

### Changed
- Updated marketing messaging and positioning
- Improved repository organization and cleanup

### Fixed
- Minor documentation issues and examples

## [0.4.0] - 2025-07-16

### Added
- **BREAKING**: Migration from PRARR to ReAct architecture (Reason → Act → Observe)
- Production hardening with metrics and reliability features
- Sequential tool execution with comprehensive error handling
- Memory relevance scoring and intelligent management
- Infinite loop detection and prevention
- Golden trace validation for testing and debugging
- Adaptive reasoning depth based on query complexity

### Changed
- **BREAKING**: Complete architecture change from PRARR to ReAct
- **BREAKING**: Tool execution model changed to sequential processing
- Enhanced tracing and visibility into reasoning steps
- Improved tool filtering and result processing
- Concurrency-safe state coordination

### Migration Guide
- Replace PRARR-based agent calls with ReAct equivalents
- Update tool execution logic for sequential processing
- Migrate custom nodes to ReAct-compatible phases

## [0.3.0] - 2025-07-12

### Added
- **BREAKING**: Stream-first execution architecture using async generators
- Real-time streaming support for all cognitive phases
- Universal LLM provider support: OpenAI, Anthropic, Gemini, Grok, Mistral
- `Agent.stream()` method for real-time execution transparency
- Built-in conversation history management
- Nomic embeddings provider integration
- Graceful cancellation support with `@cancellation` decorator

### Changed
- **BREAKING**: All nodes redesigned as async generators
- **BREAKING**: Full async/await architecture throughout codebase
- **BREAKING**: Native streaming for all LLM providers
- Standardized configuration and error handling
- Enhanced context management and state coordination

### Fixed
- Streaming compatibility across all LLM providers
- State coordination in concurrent environments

### Migration Guide
- Convert synchronous agent calls to async/await pattern
- Replace blocking operations with streaming equivalents
- Update error handling for new async patterns

## [0.2.3] - 2025-07-12

### Fixed
- DuckDuckGo Search (DDGS) integration for latest API changes
- Web search reliability and error handling

### Changed
- Updated examples and usage patterns
- Cleaned up dependency versions and compatibility

## [0.2.2] - 2025-07-12

### Added
- Live trace streaming for real-time execution visibility
- Implicit LLM key rotation and automatic failover
- Infinite recursion detection and protection

### Changed
- Enhanced error handling and parsing robustness
- Improved context management and state handling
- Better trace formatting and output processing

### Fixed
- Malformed LLM response parsing
- Edge cases in trace extraction

## [0.2.1] - 2025-07-12

### Added
- File manager tool with read/write capabilities and validation
- Modular LLM architecture with separated provider modules
- Optional trace printing with configurable output

### Changed
- Stabilized prompt engineering for consistency
- Enhanced examples with file management demonstrations
- Improved trace extraction and error formatting
- Separated LLM providers (Gemini, key rotation) for better extensibility

### Fixed
- Tool registration and discovery issues
- Error handling in trace extraction

## [0.2.0] - 2025-07-12

### Added
- PRARR cognitive architecture (Plan → Reason → Act → Reflect → Respond)
- Tool system with web search and code execution
- Full execution tracing with reasoning step visibility
- LLM orchestration with OpenAI integration
- Key rotation and response caching
- Basic CLI interface for agent interaction
- JSON-based tool routing and response parsing
- Central tool registry with automatic discovery
- 115 comprehensive unit tests

### Changed
- Multiline prompt engineering with clean formatting
- Robust error handling and output validation

## [0.1.0] - Initial Development

### Added
- Initial project setup and basic agent framework
- Core LLM instantiation and context management
- Basic tool usage and multistep reasoning capabilities
- JSON parsing and execution tracing foundation

---

## Versioning Policy

Starting with v1.0.0, this project follows [Semantic Versioning](https://semver.org/):
- **MAJOR** version for incompatible API changes
- **MINOR** version for backwards-compatible functionality additions
- **PATCH** version for backwards-compatible bug fixes

## Breaking Changes Notice

Major architectural changes are marked with **BREAKING** labels and include migration guides.
Always review the migration sections before upgrading across major versions.

[unreleased]: https://github.com/tysonchen/cogency/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/tysonchen/cogency/compare/v0.9.3...v1.0.0
[0.9.3]: https://github.com/tysonchen/cogency/compare/v0.9.2...v0.9.3
[0.9.2]: https://github.com/tysonchen/cogency/compare/v0.9.1...v0.9.2
[0.9.1]: https://github.com/tysonchen/cogency/compare/v0.9.0...v0.9.1
[0.9.0]: https://github.com/tysonchen/cogency/compare/v0.5.1...v0.9.0
[0.5.1]: https://github.com/tysonchen/cogency/compare/v0.5.0...v0.5.1
[0.5.0]: https://github.com/tysonchen/cogency/compare/v0.4.1...v0.5.0
[0.4.1]: https://github.com/tysonchen/cogency/compare/v0.4.0...v0.4.1
[0.4.0]: https://github.com/tysonchen/cogency/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/tysonchen/cogency/compare/v0.2.3...v0.3.0
[0.2.3]: https://github.com/tysonchen/cogency/compare/v0.2.2...v0.2.3
[0.2.2]: https://github.com/tysonchen/cogency/compare/v0.2.1...v0.2.2
[0.2.1]: https://github.com/tysonchen/cogency/compare/v0.2.0...v0.2.1
[0.2.0]: https://github.com/tysonchen/cogency/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/tysonchen/cogency/releases/tag/v0.1.0