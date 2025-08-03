# Contributing to Cogency

Thank you for your interest in contributing to Cogency! This guide will help you get started.

## Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/iteebz/cogency.git
   cd cogency
   ```

2. **Install dependencies**
   ```bash
   poetry install
   ```

3. **Run tests**
   ```bash
   just ci
   ```

## Architecture Overview

Cogency follows a 4-step adaptive reasoning architecture:

- **Prepare**: Context evaluation and tool selection
- **Reason**: Depth-adaptive thinking (fast react → deep reflection)  
- **Act**: Tool execution with automatic retry and recovery
- **Respond**: Identity-aware response formatting

Core components:
- **Agent**: Zero-ceremony interface (`Agent("name")`)
- **Tools**: Auto-registering capabilities with `@tool` decorator
- **Memory**: LLM-based synthesis without external dependencies
- **Runtime**: Execution engine with dependency injection

## Contributing Guidelines

### Code Style

- Follow PEP 8 for Python code style
- Use type hints for all function signatures
- Write docstrings for all public functions and classes
- Maximum line length: 100 characters (Black)

### Testing

- Write tests for all new features
- Maintain test coverage above 90%
- Use pytest for testing framework
- Mock external services in tests

### Tool Development

When creating new tools:

1. **Use the @tool decorator pattern**
   ```python
   from cogency.tools import Tool, tool
   
   @tool
   class MyTool(Tool):
       def __init__(self):
           super().__init__("my_tool", "Description")
       
       async def run(self, arg: str) -> dict:
           return {"result": f"Processed: {arg}"}
   ```

2. **Follow single responsibility principle**
   - Each tool does one thing well
   - Clear argument validation
   - Graceful error handling

3. **Add comprehensive tests**
   - Unit tests for tool logic
   - Integration tests with agent execution
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
   just ci
   ```

4. **Submit pull request**
   - Provide clear description of changes
   - Link to any related issues
   - Ensure CI tests pass

## Types of Contributions

### Core Components
Submit improvements to core execution steps:
- Must integrate with existing 4-step architecture
- Should maintain zero-ceremony interface
- Need comprehensive tests

### Tools
Add new tools that extend agent capabilities:
- Single responsibility principle
- Auto-registration via `@tool` decorator
- Comprehensive documentation

### Memory Systems
Implement memory improvements:
- Follow LLM-based synthesis pattern
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

1. **Zero Ceremony**: Simple interfaces with powerful defaults
2. **Adaptive Intelligence**: Agents think as hard as they need to
3. **Production Ready**: Built-in resilience and error handling
4. **Extensibility**: Easy tool and provider integration
5. **Clean Code**: Minimal, readable implementations

## Release Process

1. **Version Bumping**: Follow semantic versioning
2. **Changelog**: Update CHANGELOG.md with changes
3. **Testing**: Ensure all tests pass
4. **Documentation**: Update docs as needed
5. **Release**: Tag and publish to PyPI

Thank you for contributing to Cogency! Your contributions help make AI agent development more accessible and reliable.