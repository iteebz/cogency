# Node Architecture Specification

## Overview
Clean 4-node LangGraph architecture following ReAct principles with proper separation of concerns.

## Flow Diagram
```
preprocess -> reason -> act -> reason -> respond
     |                   ^      |        ^
     |                   |______|        |
     |                                   |
     |___________________________________|
     (direct response bypass)
```

## Node Specifications

### 1. Preprocess Node
**Purpose**: Routing decisions, memory extraction, tool selection  
**LLM Call**: Yes (single call for efficiency)  
**Input**: Raw user query, full tool list  
**Output**: Routing decision + filtered tools  

**Responsibilities**:
- Memory extraction (if query contains memorable info)
- Tool subsetting (exclude irrelevant tools)
- Direct response detection (bypass ReAct for simple queries)
- Save extracted memories to backend

**Prompt Goal**: "Should I enter ReAct loop or respond directly? What tools are needed? Any memories to extract?"

**Routing**:
- Direct response → `respond` node
- Needs tools → `reason` node

---

### 2. Reason Node  
**Purpose**: Pure reasoning - decide next action  
**LLM Call**: Yes (core ReAct reasoning)  
**Input**: Context + available tools + previous tool results  
**Output**: Decision (use_tool/use_tools/respond) + tool calls  

**Responsibilities**:
- Analyze current context and tool results
- Decide if more information needed
- Generate specific tool calls if needed
- Determine task completion
- **Implicit reflection** on previous tool results

**Prompt Goal**: "Based on context and tool results, what should I do next? Do I have enough info to respond?"

**Routing**:
- Need tools → `act` node
- Task complete → `respond` node

---

### 3. Act Node
**Purpose**: Pure tool execution  
**LLM Call**: No (deterministic execution)  
**Input**: Tool calls from reason node  
**Output**: Tool results added to context  

**Responsibilities**:
- Parse tool calls from reason node
- Execute single/parallel tool calls
- Handle tool errors gracefully
- Add results to context for next reason cycle
- Performance metrics tracking

**Always Routes To**: `reason` node (for reflection on results)

---

### 4. Respond Node
**Purpose**: Final response formatting and personality  
**LLM Call**: Yes (formatting + personality injection)  
**Input**: Complete context with tool results OR direct answer  
**Output**: Formatted final response  

**Responsibilities**:
- Apply personality via system prompt
- Format response for AgentInterface
- Apply response shaping rules
- Consistent tone/style across all response paths

**Prompt Goal**: "Generate final response with personality, formatting, and proper tone."

**Always Routes To**: END

## Key Design Principles

### Separation of Concerns
- **Preprocess**: Routing only
- **Reason**: Reasoning only  
- **Act**: Execution only
- **Respond**: Formatting only

### Reflection Integration
Reflection is **implicit** in the reason node when it receives tool results:
- "Did this tool help?"
- "Do I need more info?"
- "Should I try different approach?"
- "Ready to respond?"

**No separate reflection node needed** - adds ceremony without value.

### LLM Call Efficiency
- **Preprocess**: 1 call (routing + memory + tools)
- **Reason**: 1 call per cycle (reasoning + reflection)
- **Act**: 0 calls (pure execution)
- **Respond**: 1 call (formatting + personality)

### Error Handling
- Tool failures handled in `act` node
- Added to context for `reason` node to reflect on
- Reason node can retry, try different tools, or respond with partial info

### Streaming Support
Each node supports streaming callbacks for real-time user feedback on reasoning progress.