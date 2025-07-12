from cogency.llm import BaseLLM
from cogency.tools.base import BaseTool
from cogency.trace import trace_node
from cogency.types import AgentState

PLAN_PROMPT = """You are an AI assistant. Analyze the user request and respond with ONLY valid JSON.

Available tools: {tool_names}

Rules:
- Math calculations → use calculator tool
- Current info/events → use web search
- File operations → use file_manager tool
- General knowledge → direct response

Output format (choose one):

{{"action": "direct_response", "reasoning": "Brief explanation", "answer": "Your answer"}}

{{"action": "tool_needed", "reasoning": "Why tool needed", "strategy": "Which tool"}}

Respond with JSON only - no other text."""


@trace_node
def plan(state: AgentState, llm: BaseLLM, tools: list[BaseTool]) -> AgentState:
    context = state["context"]
    messages = context.messages + [{"role": "user", "content": context.current_input}]

    # Lite tool descriptions for planning decision
    if tools:
        tool_descriptions = []
        for tool in tools:
            tool_descriptions.append(f"{tool.name} ({tool.description})")
        tool_info = ", ".join(tool_descriptions)
    else:
        tool_info = "no tools"
    system_prompt = PLAN_PROMPT.format(tool_names=tool_info)
    messages.insert(0, {"role": "system", "content": system_prompt})

    llm_response = llm.invoke(messages)

    # Store the raw response for routing, but don't add to conversation yet
    context.add_message("assistant", llm_response)

    return {"context": context, "execution_trace": state["execution_trace"]}
