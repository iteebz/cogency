"""Canonical XML Streaming - The UX breakthrough for transparent AI reasoning."""

from collections.abc import AsyncGenerator
from typing import Optional

from .parsing import parse_xml_sections
from .result import Err, Result


def _streamable(llm) -> bool:
    """Canonical streaming capability detection."""
    return hasattr(llm, "stream") and callable(getattr(llm, "stream", None))


async def stream_xml_sections(llm, messages) -> Result[dict[str, Optional[str]], str]:
    """Stream XML sectioned generation with elegant boundary detection.

    The canonical streaming pattern:
    • Stream <thinking> naturally - transparent reasoning unfolds
    • Pause at <tools> boundary - reliable JSON extraction
    • Resume <response> streaming - natural conversation flow

    Returns parsed sections: {"thinking": "...", "tools": "[...]", "response": "..."}
    """
    return await (
        _stream_realtime(llm, messages) if _streamable(llm) else _parse_batch(llm, messages)
    )


async def _stream_realtime(llm, messages) -> Result[dict[str, Optional[str]], str]:
    """Stream with boundary detection - accumulate until complete."""
    buffer = ""

    try:
        async for chunk in llm.stream(messages):
            if chunk.failure:
                return chunk
            buffer += chunk.unwrap()

        return _parse_xml_buffer(buffer)

    except Exception as e:
        return Err(f"Stream error: {str(e)}")


async def _parse_batch(llm, messages) -> Result[dict[str, Optional[str]], str]:
    """Fallback batch parsing for non-streaming LLMs."""
    result = await llm.generate(messages)
    if result.failure:
        return result

    raw_response = result.unwrap()

    import logging

    logger = logging.getLogger("cogency.streaming")
    logger.debug(f"LLM response: {len(raw_response)} chars")

    parse_result = _parse_xml_buffer(raw_response)
    if parse_result.success:
        sections = parse_result.unwrap()
        logger.debug(f"XML sections parsed: {list(sections.keys())}")

    return parse_result


def _parse_xml_buffer(buffer: str) -> Result[dict[str, Optional[str]], str]:
    """Parse complete XML buffer into sections."""
    return parse_xml_sections(buffer)


async def stream_thinking(llm, messages) -> AsyncGenerator[str, None]:
    """Stream thinking content for transparent reasoning UX."""
    if not _streamable(llm):
        result = await stream_xml_sections(llm, messages)
        if result.success and result.unwrap().get("thinking"):
            yield result.unwrap()["thinking"]
        return

    buffer = ""

    try:
        async for chunk in llm.stream(messages):
            if chunk.failure:
                return

            buffer += chunk.unwrap()

            # Extract thinking when complete
            if "</thinking>" in buffer and "<thinking>" in buffer:
                start = buffer.find("<thinking>") + 10
                end = buffer.find("</thinking>")
                if start < end:
                    yield buffer[start:end].strip()
                    return

    except Exception:
        return


def validate_streaming(test_cases: list) -> bool:
    """Validate streaming implementation with test cases."""
    for i, (input_xml, expected) in enumerate(test_cases):
        result = _parse_xml_buffer(input_xml)

        if result.failure:
            print(f"Test {i + 1} FAILED: {result.error}")
            return False

        actual = result.unwrap()
        for section, expected_content in expected.items():
            if actual.get(section) != expected_content:
                print(f"Test {i + 1} FAILED: {section} mismatch")
                return False

    return True
