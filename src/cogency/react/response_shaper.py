
"""Response shaping system - transforms raw cognitive output into final format."""
import json
from typing import Dict, Any, Optional, Union
from cogency.llm import BaseLLM


class ResponseShaper:
    """Transforms raw cognitive output into desired format/tone/style."""

    def __init__(self, llm: BaseLLM):
        self.llm = llm

    async def shape(self, raw_response: str, config: Dict[str, Any]) -> Union[str, Dict[str, Any]]:
        """Shape raw response according to config."""
        if not config:
            return raw_response

        # Check if intent signals should be emitted
        emit_intent_signals = config.get("emit_intent_signals", False)

        # Build shaping prompt from config
        shaping_prompt = self._build_shaping_prompt(config, emit_intent_signals)

        messages = [
            {"role": "system", "content": shaping_prompt},
            {"role": "user", "content": f"Transform this response:\n\n{raw_response}"}
        ]

        shaped_response = await self.llm.invoke(messages)

        # If intent signals requested, parse and return structured response
        if emit_intent_signals:
            return self._parse_response_with_intent(shaped_response)

        return shaped_response

    def _build_shaping_prompt(self, config: Dict[str, Any], emit_intent_signals: bool = False) -> str:
        """Build shaping prompt from config."""
        prompt_parts = ["Transform the following response according to these specifications:"]

        # Format transformation
        if "format" in config:
            format_type = config["format"]
            if format_type == "multi-aip-json":
                prompt_parts.append(self._get_aip_format_instructions())
            elif format_type == "markdown":
                prompt_parts.append("- Format as clean markdown")
            elif format_type == "html":
                prompt_parts.append("- Format as semantic HTML")

        # Tone and style
        if "tone" in config:
            prompt_parts.append(f"- Use {config['tone']} tone")

        if "style" in config:
            prompt_parts.append(f"- Apply {config['style']} style")

        # Constraints
        if "constraints" in config:
            for constraint in config["constraints"]:
                prompt_parts.append(f"- {constraint.replace('-', ' ').title()}")

        # Transformations
        if "transformations" in config:
            for transform in config["transformations"]:
                prompt_parts.append(f"- {transform.replace('-', ' ').title()}")

        # Intent signal emission instructions
        if emit_intent_signals:
            prompt_parts.append("\nADDITIONALLY, wrap your response in a JSON structure:")
            prompt_parts.append('{"content": "your_transformed_response", "intent_signals": {"primary_intent": "...", "content_type": "...", "user_context": "...", "complexity": "..."}}')
            prompt_parts.append("\nIntent signal guidelines:")
            prompt_parts.append("- primary_intent: showcase_work, explain_concept, show_timeline, show_code, show_writing, summarize, etc.")
            prompt_parts.append("- content_type: project_list, code_sample, essay, timeline, summary, explanation, etc.")
            prompt_parts.append("- user_context: professional_inquiry, casual_browsing, technical_review, etc.")
            prompt_parts.append("- complexity: overview, detailed, comprehensive")

        return "\n".join(prompt_parts)

    def _get_aip_format_instructions(self) -> str:
        """Get AIP format instructions."""
        return """- Format as MULTI-AIP JSON - series of AIP-compliant JSON objects, each on its own line\n\nAvailable interface types:\n- markdown: {"type": "markdown", "content": "text"}\n- blog-post: {"type": "blog-post", "data": {"title": "Title", "content": "Content", "metadata": {}}}\n- card-grid: {"type": "card-grid", "data": {"cards": [{"title": "Name", "description": "Desc", "tags": [], "links": [], "metadata": {}}]}}\n- code-snippet: {"type": "code-snippet", "data": {"code": "console.log('hello')", "language": "javascript"}}\n- expandable-section: {"type": "expandable-section", "data": {"sections": [{"title": "Title", "content": "Content", "defaultExpanded": false}]}}\n- inline-reference: {"type": "inline-reference", "data": {"references": [{"id": "ref1", "title": "Title", "type": "project", "excerpt": "Brief", "content": "Full content"}]}}\n- key-insights: {"type": "key-insights", "data": {"insights": [{"title": "Insight", "description": "Description", "category": "category"}]}}\n- timeline: {"type": "timeline", "data": {"events": [{"date": "2025", "title": "Event", "description": "Desc"}]}}\n\nUse expandable-section for CoT reasoning, key-insights for analysis, and mix narrative with structured data."""

    def _parse_response_with_intent(self, shaped_response: str) -> Dict[str, Any]:
        """Parse response that includes intent signals."""
        try:
            # Try to parse as JSON first
            parsed = json.loads(shaped_response)
            if "content" in parsed and "intent_signals" in parsed:
                return parsed
        except json.JSONDecodeError:
            pass

        # Fallback: extract JSON from response if wrapped in other content
        try:
            # Look for JSON block in response
            start_idx = shaped_response.find('{')
            end_idx = shaped_response.rfind('}') + 1
            if start_idx != -1 and end_idx > start_idx:
                json_str = shaped_response[start_idx:end_idx]
                parsed = json.loads(json_str)
                if "content" in parsed and "intent_signals" in parsed:
                    return parsed
        except (json.JSONDecodeError, ValueError):
            pass

        # Ultimate fallback: return raw response with minimal intent signals
        return {
            "content": shaped_response,
            "intent_signals": {
                "primary_intent": "general_response",
                "content_type": "text",
                "user_context": "unknown",
                "complexity": "overview"
            }
        }


# Prebuilt shaping profiles
SHAPING_PROFILES = {
    "folio_aip": {
        "format": "multi-aip-json",
        "tone": "professional-approachable",
        "style": "technical-precision-human-warmth",
        "constraints": ["use-first-person", "include-reasoning"],
        "transformations": ["add-cot-expandable", "highlight-key-insights"]
    },
    "markdown_clean": {
        "format": "markdown",
        "tone": "clear-concise",
        "style": "technical-documentation"
    },
    "conversational": {
        "tone": "friendly-helpful",
        "style": "natural-dialogue",
        "constraints": ["use-contractions", "ask-clarifying-questions"]
    }
}

async def shape_response(
    raw_response: str,
    llm: BaseLLM,
    profile: Optional[str] = None,
    custom_config: Optional[Dict[str, Any]] = None
) -> Union[str, Dict[str, Any]]:
    """Shape response using prebuilt profile or custom config."""
    if custom_config:
        config = custom_config
    elif profile and profile in SHAPING_PROFILES:
        config = SHAPING_PROFILES[profile]
    else:
        return raw_response

    shaper = ResponseShaper(llm)
    return await shaper.shape(raw_response, config)


async def apply_response_shaping(text: str, llm: BaseLLM, shaper_config: Optional[Dict[str, Any]]) -> str:
    """Apply response shaping if configured, otherwise return text unchanged."""
    if not shaper_config:
        return text

    shaper = ResponseShaper(llm)
    shaped_text = await shaper.shape(text, shaper_config)

    if isinstance(shaped_text, dict):
        return shaped_text.get("content", "")

    return shaped_text
