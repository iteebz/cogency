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
   pip install -e ".[all]"
   ```

3. **Run tests**
   ```bash
   pytest
   ```

## Architecture Overview

Cogency follows a layered architecture:

- **Skills**: Cognitive operations (analyze, extract, synthesize)
- **Tools**: Smart wrappers around services with behavior
- **Services**: Raw capabilities (LLM, embedding, etc.)

See `docs/architecture.md` for detailed architecture documentation.

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

### Skills Development

When adding new skills:

1. **Follow the cognitive verb pattern**
   ```python
   @skill(
       name="your_skill",
       description="Clear description of cognitive operation",
       category="cognitive",
       author="your_name"
   )
   async def your_skill(context: SkillContext, **params) -> SkillResult:
       # Implementation
   ```

2. **Use tool orchestration**
   - Skills should orchestrate tools, not implement logic
   - Add graceful degradation with fallbacks
   - Return structured SkillResult objects

3. **Add comprehensive tests**
   - Unit tests for skill logic
   - Integration tests with mocked services
   - Error handling scenarios

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
   pytest
   mypy cogency
   ruff check cogency
   ```

4. **Submit pull request**
   - Provide clear description of changes
   - Link to any related issues
   - Ensure CI tests pass

## Types of Contributions

### Core Skills
Submit new cognitive operations that follow the skill pattern:
- Must be atomic (single responsibility)
- Should have clear cognitive purpose
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

1. **Cognitive Clarity**: Code should map directly to mental processes
2. **Composability**: Skills should work together seamlessly
3. **Reliability**: Graceful degradation under failure
4. **Extensibility**: Easy to add new capabilities
5. **Maintainability**: Clean abstractions and clear boundaries

## Release Process

1. **Version Bumping**: Follow semantic versioning
2. **Changelog**: Update CHANGELOG.md with changes
3. **Testing**: Ensure all tests pass
4. **Documentation**: Update docs as needed
5. **Release**: Tag and publish to PyPI

Thank you for contributing to Cogency! Your contributions help make AI agent development more accessible and reliable.