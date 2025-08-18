"""Agent: React-enabled reasoning interface."""

import time
from contextlib import suppress

from ..context import context, persist
from ..lib.parsing import parse_with_signature
from ..lib.providers import create_embedder, create_llm
from ..tools import BASIC_TOOLS
from .types import AgentResult


class Agent:
    """Agent with React reasoning and tool execution."""

    def __init__(self, llm="openai", embedder=None, tools=None, max_iterations: int = 5):
        self.llm = create_llm(llm)
        self.embedder = create_embedder(embedder) if embedder else None
        self.tools = {t.name: t for t in (tools if tools is not None else BASIC_TOOLS)}
        self.max_iterations = max_iterations

    async def __call__(self, query: str, user_id: str = "default") -> AgentResult:
        """Execute query with React reasoning."""
        tool_results = []

        for _iteration in range(self.max_iterations):
            # Build context with tools and results
            ctx = context(query, user_id, tool_results)
            prompt = self._build_prompt(query, ctx, tool_results)

            # Use provider system with single canonical path
            llm_result = await self._generate_response(prompt)
            if llm_result.failure:
                return AgentResult(
                    f"LLM Error: {llm_result.error}", f"{user_id}_{int(time.time())}"
                )

            response = llm_result.unwrap()

            # Parse for completion or tool use
            if "final answer" in response.lower():
                final = self._extract_final_answer(response)
                conversation_id = f"{user_id}_{int(time.time())}"
                with suppress(Exception):
                    await persist(user_id, query, final)
                return AgentResult(final, conversation_id)

            # Execute tool if found
            tool_used = await self._execute_tool(response, tool_results)
            if not tool_used:
                # No tool found, return response as-is
                conversation_id = f"{user_id}_{int(time.time())}"
                with suppress(Exception):
                    await persist(user_id, query, response)
                return AgentResult(response, conversation_id)

        # Max iterations reached - return last response
        conversation_id = f"{user_id}_{int(time.time())}"
        with suppress(Exception):
            await persist(user_id, query, response)
        return AgentResult(response, conversation_id)

    async def _generate_response(self, prompt: str):
        """Generate response using configured LLM - single canonical path."""
        messages = [{"role": "user", "content": prompt}]
        return await self.llm.generate(messages)

    def _build_prompt(self, query: str, ctx: str, tool_results: list) -> str:
        """Build React prompt with context and tools."""
        parts = []
        if ctx.strip():
            parts.append(ctx)

        parts.append(f"TASK: {query}")

        if self.tools:
            tools_text = "\n".join(f"- {t.name}: {t.description}" for t in self.tools.values())
            parts.append(f"TOOLS:\n{tools_text}")

        if tool_results:
            results_text = "PREVIOUS TOOLS:\n"
            for r in tool_results[-3:]:
                name = r["tool"]
                if "result" in r:
                    results_text += f"✅ {name}: {str(r['result'])[:200]}...\n"
                else:
                    results_text += f"❌ {name}: {str(r.get('error', 'Unknown error'))}\n"
            parts.append(results_text)

        prompt = "\n\n".join(parts)
        return f"""{prompt}

Think step by step. Use tools when needed by writing:
USE: tool_name(arg1="value1", arg2="value2")

When complete, write your final answer."""

    async def _generate_response(self, prompt: str):
        """Generate response using configured LLM provider."""
        messages = [{"role": "user", "content": prompt}]
        return await self.llm.generate(messages)

    async def _execute_tool(self, response: str, tool_results: list) -> bool:
        """Execute tool from response. Returns True if tool was used."""
        # First, extract tool name to get tool instance
        import re

        match = re.search(r"USE:\s*(\w+)\(", response, re.IGNORECASE)
        if not match:
            return False

        tool_name = match.group(1)
        if tool_name not in self.tools:
            result_entry = {"tool": tool_name, "args": {}, "error": f"Unknown tool: {tool_name}"}
            tool_results.append(result_entry)
            return True

        # Use signature-based parsing with the actual tool instance
        parse_result = parse_with_signature(response, self.tools[tool_name])
        if parse_result.failure:
            return False

        call_data = parse_result.unwrap()
        args = call_data["args"]

        result_entry = {"tool": tool_name, "args": args}

        try:
            result = await self.tools[tool_name].execute(**args)
            if result.success:
                result_entry["result"] = result.unwrap()
            else:
                result_entry["error"] = result.error
        except Exception as e:
            result_entry["error"] = str(e)

        tool_results.append(result_entry)
        return True

    def _extract_final_answer(self, response: str) -> str:
        """Extract final answer from response."""
        lower_response = response.lower()
        if "final answer:" in lower_response:
            # Find the position of "final answer:" (case insensitive)
            pos = lower_response.find("final answer:")
            return response[pos + len("final answer:") :].strip()
        return response
