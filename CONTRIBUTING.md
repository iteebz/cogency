# Contributing to Cogency

Thank you for your interest in contributing to Cogency! This guide will help you get started.

## Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/cogencyai/cogency.git
   cd cogency
   ```

2. **Install dependencies**
   ```bash
   poetry install --all-extras
   ```

3. **Run tests**
   ```bash
   poetry run pytest
   ```

## Architecture Overview

Cogency follows a phase-based cognitive architecture:

- **Phases**: ReAct cognitive stages (Prepare → Reason → Act → Respond)
- **Tools**: Extensible capabilities with automatic discovery
- **Services**: Provider backends (LLM, embedding, memory)
- **Memory**: Persistent conversation context

See `NAVIGATION.md` for detailed architecture documentation.

## Contributing Guidelines

### Code Style

- Follow PEP 8 for Python code style
- Use type hints for all function signatures
- Write docstrings for all public functions and classes
- Maximum line length: 88 characters

### Testing

- Write tests for all new features
- Maintain test coverage above 90%
- Use pytest for testing framework
- Mock external services in tests

### Phase Development

When extending phases:

1. **Follow the @phase decorator pattern**
   ```python
   @phase(name="custom_step")
   async def custom_step(state: State, **kwargs):
       # Implementation with automatic robustness, observability
       return result
   ```

2. **Use dependency injection**
   - Phases receive dependencies (LLM, tools, memory) automatically
   - Focus on cognitive logic, not service orchestration
   - State flows through phases immutably

3. **Add comprehensive tests**
   - Unit tests for phase logic
   - Integration tests with mocked services
   - Error handling and recovery scenarios

### Pull Request Process

1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Follow the coding standards
   - Add tests for new functionality
   - Update documentation as needed

3. **Run the test suite**
   ```bash
   poetry run pytest
   poetry run ruff check src/
   poetry run ruff check src/cogency
   ```

4. **Submit pull request**
   - Provide clear description of changes
   - Link to any related issues
   - Ensure CI tests pass

## Types of Contributions

### Core Phases
Submit new cognitive phases that follow the @phase pattern:
- Must be atomic (single cognitive step)
- Should integrate with ReAct architecture
- Need comprehensive tests

### Tools
Add new tools that wrap services with smart behavior:
- Single responsibility principle
- Graceful error handling
- Comprehensive documentation

### Services
Implement service interfaces for new providers:
- Follow existing service patterns
- Add configuration options
- Include integration tests

### Documentation
Improve documentation:
- Architecture explanations
- Usage examples
- API documentation
- Tutorials

## Issue Reporting

When reporting issues:

1. **Use the issue template**
2. **Provide minimal reproduction case**
3. **Include environment information**
4. **Describe expected vs actual behavior**

## Questions and Support

- **Documentation**: Check `docs/` directory
- **Issues**: Use GitHub issues for bug reports
- **Discussions**: Use GitHub discussions for questions

## Code of Conduct

- Be respectful and inclusive
- Welcome newcomers and help them learn
- Focus on constructive feedback
- Maintain professional communication

## Development Philosophy

Cogency prioritizes:

1. **Zero Ceremony**: Magical defaults with opt-in complexity
2. **Beautiful Abstractions**: Complex functionality with simple interfaces  
3. **Reliability**: @robust decorator handles failures gracefully
4. **Extensibility**: Provider pattern for infinite backends
5. **Maintainability**: Clean code doctrine, no bullshit patterns

## Release Process

1. **Version Bumping**: Follow semantic versioning
2. **Changelog**: Update CHANGELOG.md with changes
3. **Testing**: Ensure all tests pass
4. **Documentation**: Update docs as needed
5. **Release**: Tag and publish to PyPI

Thank you for contributing to Cogency! Your contributions help make AI agent development more accessible and reliable.