"""Multi-provider evaluation - test cogency across different LLM providers."""

import os
from typing import List

from cogency import Agent
from cogency.providers.llm import Anthropic, Gemini, Mistral, OpenAI
from evals.core import Eval, EvalResult


class MultiProviderEval(Eval):
    """Test cogency across multiple LLM providers with same query."""

    name = "multi_provider"
    description = "Test agent consistency across different LLM providers"

    def _get_available_providers(self) -> List[tuple[str, type]]:
        """Get providers with available API keys."""
        providers = []

        if os.getenv("GEMINI_API_KEY"):
            providers.append(("gemini", Gemini))
        if os.getenv("OPENAI_API_KEY"):
            providers.append(("openai", OpenAI))
        if os.getenv("ANTHROPIC_API_KEY"):
            providers.append(("anthropic", Anthropic))
        if os.getenv("MISTRAL_API_KEY"):
            providers.append(("mistral", Mistral))

        return providers

    async def run(self) -> EvalResult:
        providers = self._get_available_providers()

        if len(providers) < 2:
            return self.fail(
                f"Need at least 2 providers, found {len(providers)}: {[p[0] for p in providers]}"
            )

        query = "What is the capital of France? Answer with just the city name."
        expected = "Paris"

        results = {}
        errors = []

        for provider_name, provider_class in providers:
            try:
                llm = provider_class()
                agent = Agent(f"test_{provider_name}", llm=llm, memory=False)
                response = await agent.run(query)

                # Check if Paris is in the response
                passed = expected.lower() in response.lower()
                results[provider_name] = {"response": response, "passed": passed}
            except Exception as e:
                errors.append(f"{provider_name}: {e}")
                results[provider_name] = {"response": None, "passed": False, "error": str(e)}

        # Calculate overall success
        successful_providers = sum(1 for r in results.values() if r["passed"])
        total_providers = len(providers)
        score = successful_providers / total_providers
        passed = score >= 0.5  # Pass if at least half work

        metadata = {
            "query": query,
            "expected": expected,
            "providers_tested": total_providers,
            "providers_passed": successful_providers,
            "results": results,
            "errors": errors,
        }

        if errors:
            error_msg = "; ".join(errors)
        else:
            error_msg = None

        return EvalResult(
            name=self.name,
            passed=passed,
            score=score,
            duration=0.0,  # Will be filled by base class
            expected=f"{successful_providers}/{total_providers} providers working",
            actual=f"{successful_providers}/{total_providers} providers working",
            error=error_msg,
            metadata=metadata,
        )
