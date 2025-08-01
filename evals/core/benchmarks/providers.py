"""Provider benchmarking - cross-provider performance and consistency analysis."""

import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from cogency.providers.llm import Anthropic, Gemini, Mistral, OpenAI
from evals.core.benchmarks.core import benchmark_eval


@dataclass
class ProviderBenchmark:
    """Benchmark results for a single provider."""

    provider_name: str
    model: str
    success: bool
    error: Optional[str] = None
    phase_timing: Optional[Dict] = None
    system_metrics: Optional[Dict] = None
    eval_result: Optional[Dict] = None


@dataclass
class CrossProviderResults:
    """Aggregated benchmarking results across multiple providers."""

    eval_name: str
    query: str
    providers: List[ProviderBenchmark] = field(default_factory=list)
    success_rate: float = 0.0
    fastest_provider: Optional[str] = None
    slowest_provider: Optional[str] = None

    def add_provider(self, benchmark: ProviderBenchmark) -> None:
        """Add provider benchmark results."""
        self.providers.append(benchmark)
        self._update_metrics()

    def _update_metrics(self) -> None:
        """Update aggregated metrics."""
        if not self.providers:
            return

        # Success rate
        successful = sum(1 for p in self.providers if p.success)
        self.success_rate = successful / len(self.providers)

        # Speed comparison (based on total duration)
        durations = []
        for p in self.providers:
            if p.success and p.phase_timing and p.phase_timing.get("total_duration"):
                durations.append((p.provider_name, p.phase_timing["total_duration"]))

        if durations:
            durations.sort(key=lambda x: x[1])
            self.fastest_provider = durations[0][0]
            self.slowest_provider = durations[-1][0]


def get_available_providers() -> List[Tuple[str, type, str]]:
    """Get providers with available API keys and their default models."""
    providers = []

    if os.getenv("ANTHROPIC_API_KEY"):
        providers.append(("anthropic", Anthropic, "claude-3-haiku-20240307"))
    if os.getenv("OPENAI_API_KEY"):
        providers.append(("openai", OpenAI, "gpt-4o-mini"))
    if os.getenv("GEMINI_API_KEY"):
        providers.append(("gemini", Gemini, "gemini-1.5-flash"))
    if os.getenv("MISTRAL_API_KEY"):
        providers.append(("mistral", Mistral, "mistral-small-latest"))

    return providers


async def benchmark_providers(eval_instance, min_providers: int = 1) -> CrossProviderResults:
    """Benchmark a single evaluation across all available providers."""
    providers = get_available_providers()

    if len(providers) < min_providers:
        available = [p[0] for p in providers]
        raise ValueError(
            f"Need at least {min_providers} providers, found {len(providers)}: {available}"
        )

    results = CrossProviderResults(
        eval_name=eval_instance.name, query=getattr(eval_instance, "description", "Unknown eval")
    )

    for provider_name, provider_class, model in providers:
        try:
            # Create provider-specific LLM
            llm = provider_class(model=model)

            # Create a new eval instance with provider-specific LLM injection
            provider_eval = type(eval_instance)()
            provider_eval.name = f"{eval_instance.name}_{provider_name}"

            # Monkey patch the eval to use this specific provider
            original_run = provider_eval.run

            async def provider_run(captured_llm=llm, captured_original_run=original_run):
                """Run eval with provider-specific LLM injected into Agent creation."""
                # Monkey patch Agent creation to use our LLM
                from cogency import Agent

                original_agent_init = Agent.__init__

                def patched_init(self, *args, **kwargs):
                    # Inject our provider's LLM
                    kwargs["llm"] = captured_llm
                    return original_agent_init(self, *args, **kwargs)

                Agent.__init__ = patched_init

                try:
                    result = await captured_original_run()
                    return result
                finally:
                    # Restore original
                    Agent.__init__ = original_agent_init

            provider_eval.run = provider_run

            # Benchmark this provider
            provider_benchmark = await benchmark_eval(provider_eval)

            # Extract success from eval result
            eval_result = provider_benchmark.get("eval_result")
            success = eval_result.passed if eval_result else False

            results.add_provider(
                ProviderBenchmark(
                    provider_name=provider_name,
                    model=model,
                    success=success,
                    phase_timing=provider_benchmark.get("phase_timing"),
                    system_metrics=provider_benchmark.get("system_metrics"),
                    eval_result=eval_result.__dict__ if eval_result else None,
                )
            )

        except Exception as e:
            results.add_provider(
                ProviderBenchmark(
                    provider_name=provider_name, model=model, success=False, error=str(e)
                )
            )

    return results


def format_provider_comparison(results: CrossProviderResults) -> str:
    """Format cross-provider results for console output."""
    lines = []
    lines.append(f"\n🔥 Cross-Provider Benchmark: {results.eval_name}")
    lines.append(f"📊 Success Rate: {results.success_rate:.1%}")

    if results.fastest_provider and results.slowest_provider:
        lines.append(f"⚡ Fastest: {results.fastest_provider}")
        lines.append(f"🐌 Slowest: {results.slowest_provider}")

    lines.append("\nProvider Results:")
    for provider in results.providers:
        status = "✅" if provider.success else "❌"
        duration = ""
        if provider.phase_timing and provider.phase_timing.get("total_duration"):
            total = provider.phase_timing.get("total_duration", 0)
            duration = f" ({total:.2f}s)"

        error_info = f" - {provider.error}" if provider.error else ""
        lines.append(
            f"  {status} {provider.provider_name} ({provider.model}){duration}{error_info}"
        )

    return "\n".join(lines)
