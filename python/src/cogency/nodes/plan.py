from cogency.llm import BaseLLM
from cogency.tools.base import BaseTool
from cogency.trace import trace_node
from cogency.types import AgentState

PLAN_PROMPT = """
You are an AI assistant. Your goal is to help the user.
You have access to the following tools: {tool_names}.
CRITICAL: For ANY math calculation, you MUST use the calculator tool, even for simple math.
NEVER do math in your head - always use the calculator tool.
Only give direct responses for non-math questions.
Your output MUST be a single, valid JSON object and nothing else. Do not add any text before or after the JSON.
Choose one of the following JSON structures for your response:
- If you can answer directly WITHOUT tools: {{"action": "direct_response", "reasoning": "I can answer this directly because...", "answer": "<your answer>"}}
- If you need a tool: {{"action": "tool_needed", "reasoning": "<Why you need a tool>", "strategy": "<Which tool you will use>"}}
"""


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
