# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2024-07-10

### Added
- Initial release of cogency cognitive architecture framework
- Core Skills: analyze, extract, synthesize cognitive operations
- Service abstractions: LLMService, EmbeddingService interfaces
- Tool orchestration: ContentAnalysisTool, ContentExtractionTool
- Dual-mode skill registry system (manual wiring + auto-discovery)
- Comprehensive type hints and error handling
- CLI tools for skill management and documentation
- Integration tests for end-to-end workflows
- Structured error handling with graceful degradation
- Dependency injection system for services and tools
- Skill factory pattern for dynamic skill creation
- Documentation generation from skill metadata
- Support for skill aliases and categorization

### Architecture
- Clean separation of concerns: Skills → Tools → Services
- Universal interface pattern for perfect composability
- Cognitive primitives aligned with natural language
- Framework-agnostic design for maximum portability
- Atomic operations with single responsibility principle

### Dependencies
- pydantic>=2.0 for data validation
- typing-extensions>=4.0 for advanced type hints
- Optional dependencies for different LLM providers

[Unreleased]: https://github.com/cogencyai/cogency/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/cogencyai/cogency/releases/tag/v0.1.0