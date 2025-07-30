# Cogency v0.9.0 - Production Beta

**Release Date**: July 30, 2025  
**Status**: Production Beta - Architecturally complete, ready for serious evaluation

## 🎯 What's New

Cogency v0.9.0 represents a complete architectural foundation for building intelligent AI agents with zero ceremony and full semantic capability.

### 🧠 Core Features

**Adaptive Reasoning Engine**
- Automatic fast/deep mode switching based on task complexity
- Semantic state summarization replaces mechanical control flow
- Clean 4-phase execution: preprocess → reason → act → respond

**Zero Ceremony API**
```python
from cogency import Agent
agent = Agent("assistant")
result = await agent.run("What's 2+2?")
```

**Progressive Complexity**
- 3-line demos to full research agents
- Optional flags for observability, persistence, robustness
- Auto-detection for LLMs, tools, memory backends

**Built-in Tool Ecosystem**
- 14 production-ready tools (Calculator, Weather, Search, Files, etc.)
- Automatic tool discovery and intelligent routing
- Simple decorator-based custom tool creation

**Memory & Persistence**  
- Multiple backends: Pinecone, ChromaDB, PGVector, Filesystem
- Automatic conversation context and semantic search
- Built-in checkpointing and recovery

**Universal LLM Support**
- OpenAI, Anthropic, Gemini, Grok, Mistral out of the box
- Consistent behavior across providers (in progress)
- Auto-detection from environment variables

## 🚧 Beta Status

This is production beta software. Core functionality is stable and tested (292+ unit tests), but we're actively gathering feedback on:

- **Cross-provider behavior consistency** - Some edge cases remain
- **Memory backend robustness** - Real-world deployment validation needed
- **Error handling for external users** - Ongoing refinement

## 🚀 Getting Started

```bash
pip install cogency
export OPENAI_API_KEY=sk-...  # or ANTHROPIC_API_KEY, etc.
```

```python
from cogency import Agent

# Simple usage
agent = Agent("assistant")
result = await agent.run("Weather in Tokyo?")

# Advanced configuration
agent = Agent(
    "researcher", 
    mode="deep",
    memory=True,
    robust=True,
    observe=True
)
```

## 📚 Documentation

- **[Quick Start](docs/quickstart.md)** - 5-minute setup guide
- **[API Reference](docs/api.md)** - Complete documentation
- **[Examples](examples/)** - Working code samples
- **[Tools](docs/tools.md)** - Built-in and custom tools

## 🐛 Known Issues & Feedback

**Report Issues**: [GitHub Issues](https://github.com/iteebz/cogency/issues)  
**Discussions**: [GitHub Discussions](https://github.com/iteebz/cogency/discussions)

**Known Limitations**:
- Cross-provider behavior may vary (OpenAI/Anthropic most stable)
- Memory backends need more real-world validation
- Some error messages still developer-focused

## 🎉 What's Next

**v1.0.0 Goals**:
- Full cross-provider behavior consistency
- Comprehensive memory backend validation  
- External user experience polish
- Community feedback integration

## 📄 Technical Details

**Architecture**: Clean dependency injection, semantic summarization, resilient decorators  
**Testing**: 292 unit tests, integration test suite, cross-provider validation  
**Dependencies**: Minimal core, optional heavy dependencies (ChromaDB, etc.)  
**Python**: 3.10+ support, async-first design

---

**Ready to build intelligent agents?** This beta is architecturally complete and ready for serious projects. Join our early adopter community and help shape v1.0.0.