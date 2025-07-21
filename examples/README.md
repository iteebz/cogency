# Cogency Examples

Clean, focused examples showcasing Cogency's core capabilities.

## Core Examples

Run these in order to understand Cogency's progression:

### 1. `hello.py` - Conversation + Response Shaping
```bash
python hello.py
```
- Basic agent functionality
- Response shaping and personality
- Interactive conversation with context

### 2. `memory.py` - Persistent Memory  
```bash
python memory.py
```
- Cross-session memory persistence
- Intelligent information retention
- Core architectural differentiator

### 3. `research.py` - Multi-Tool Coordination
```bash
python research.py
```
- Complex multi-step reasoning
- Intelligent tool selection
- Sequential tool dependencies

### 4. `coding.py` - Code Execution
```bash
python coding.py
```
- Complete coding workflows
- Tool subsetting for specialization
- File I/O + code execution

## Development Scripts

Located in `dev/` folder for advanced users:

### `dev/config.py` - Configuration Reference
```bash
python dev/config.py
```
Shows all agent configuration options and patterns.

### `dev/tracing.py` - Debug Tracing
```bash
python dev/tracing.py
```
Demonstrates execution tracing for development and debugging.

## Progression

**Chat → Remember → Reason → Code**

Each example builds conceptually while demonstrating tool subsetting:

- **hello.py**: 0 tools (pure conversation)
- **memory.py**: 1 tool (recall only)  
- **research.py**: 4 tools (focused research toolkit)
- **coding.py**: 3 tools (focused coding environment)

Shows tool subsetting as a real feature, not just theory.

## Archived Examples

Previous examples are preserved in `archive/` folder for reference.