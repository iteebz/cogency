# Cogency Philosophy: Tools > Nodes

## The Abstraction Level Leap

Cogency represents a fundamental shift in how we think about agent frameworks. Instead of composing at the node level (orchestration), we compose at the tool level (capabilities).

### The Old Way: Node Composition
```python
# LangGraph: Wire nodes together
graph.add_node("reasoning", reason_function)
graph.add_node("action", action_function)  
graph.add_conditional_edges("reasoning", router)
```

### The New Way: Tool Composition
```python
# Cogency: Compose capabilities
agent = Agent("assistant", tools=[search, calculator, files])
agent.run("Analyze this data")
```

## Why This Matters

**Mental Model Alignment**: Developers think "I need an agent that can search and calculate" not "I need to wire reasoning nodes to action nodes."

**Reusability**: Same agent architecture, different tool combinations. No rewiring graphs.

**Abstraction Hiding**: The reasoning pipeline is solved once, perfectly. Developers focus on domain tools.

**Natural Composability**: Tools compose naturally. Node graphs require explicit wiring ceremony.

## The Pipeline: Solved Once

Cogency canonizes the agent execution pattern:

```python
preprocess() → reason() → act() → respond()
```

- **preprocess**: Efficiency gains and routing
- **reason**: Pure reasoning and decision making  
- **act**: Tool execution
- **respond**: Output shaping and interface integration

This pipeline is solved at the framework level. Developers work where the business value lives: **tools**.

## The Compiler Analogy

Think of it this way:
- **Assembly (Node frameworks)**: Wire individual instructions
- **High-level language (Cogency)**: Call functions, get results

Cogency is the compiler. You write the programs (tool combinations).

## Evolution, Not Alternative

This isn't "another LangGraph" - it's what comes after graph thinking. Tools are the right composition primitive because they match how humans think about agent capabilities.

When you want an agent that can "research and write reports," you're thinking tools, not nodes.

## Build Right, Once

The agent orchestration problem gets solved at the framework level. The reasoning loop, error handling, state management, and execution flow are perfected once.

Developers compose at the tool level where creativity and domain expertise matter most.

This is the natural evolution: from wiring nodes to composing capabilities.