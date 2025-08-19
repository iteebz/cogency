"""Canonical XML parsing for structured LLM responses."""

import re
from typing import Optional

from .result import Err, Ok, Result


def parse_xml_sections(xml_buffer: str) -> Result[dict[str, Optional[str]], str]:
    """Parse XML buffer into thinking, tools, and response sections.

    Args:
        xml_buffer: XML content with <thinking>, <tools>, <response> sections

    Returns:
        Result with dict containing sections: {"thinking": "...", "tools": "...", "response": "..."}
        Missing sections are None.
    """
    if not xml_buffer or not xml_buffer.strip():
        return Ok({"thinking": None, "tools": None, "response": None})

    try:
        sections = {}

        # Parse each section with case-insensitive regex
        for section in ["thinking", "tools", "response"]:
            pattern = rf"<{section}>\s*(.*?)\s*</{section}>"
            match = re.search(pattern, xml_buffer, re.IGNORECASE | re.DOTALL)

            if match:
                content = match.group(1).strip()
                sections[section] = content if content else None
            else:
                sections[section] = None

        return Ok(sections)

    except Exception as e:
        return Err(f"XML parsing failed: {str(e)}")
